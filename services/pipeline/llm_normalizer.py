"""
Stage 2 — Transform via LiteRTLM (staging.raw_crawl → staging.normalized_products)

For each row in staging.raw_crawl with llm_status='pending':
  1. Pre-clean raw_name with ProductNormalizer (reduce noise in prompt)
  2. Batch N names into one LiteRTLM stateless conversation request
  3. Parse structured JSON response:
       { product_type, brand, model, specs: [{name, value}, ...] }
  4. Derive normalized_name in code from structured fields (not from LLM)
  5. Write results to staging.normalized_products
  6. Mark llm_status='done' on success, 'failed' on parse error

normalized_name derivation:
  "<brand> <model> <spec_value1> <spec_value2> ..."  → lowercased, ASCII-safe
  Used for Typesense product dedup and indexing.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import uuid
from typing import Any

import requests

from services.crawler.utils.text_parser import ProductNormalizer
from services.pipeline.config import (
    LITELLM_BASE_URL,
    LITELLM_API_KEY,
    LITELLM_USERNAME,
    LITELLM_PASSWORD,
    LLM_BATCH_SIZE,
    LLM_MAX_RETRIES,
)


_normalizer = ProductNormalizer()

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
You are a data normalizer for Vietnamese tech e-commerce products.

You will receive a numbered list of raw product names (may be in Vietnamese or mixed language).
For each name return one JSON object in a JSON array (same order, same count).

Each object must have exactly these fields:
  "product_type" : the type of product in English, lowercase
                   e.g. "smartphone", "laptop", "tablet", "headphone", "speaker",
                        "monitor", "keyboard", "mouse", "pc", "smart watch",
                        "air conditioner", "refrigerator", "washing machine",
                        "accessory", or another short English noun — never null
  "brand"        : brand / manufacturer name in Title Case, or null if unknown
  "model"        : model name / number in its canonical form (Title Case), or null
                   e.g. "iPhone 15 Pro Max", "Galaxy S24 Ultra", "WH-1000XM5"
  "specs"        : array of {{ "name": <string>, "value": <string> }} objects
                   covering RAM, ROM/storage, color, connectivity, screen size, etc.
                   Use English names for spec keys. Empty array [] if no specs found.

Rules:
- Translate everything to English.
- Remove marketing terms (e.g. "chính hãng", "freeship", "trả góp", "flash sale").
- If a field cannot be determined, use null (except specs which is always an array).
- Return ONLY a valid JSON array — no markdown, no explanation, no extra text.

Raw names:
{names}"""


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _get_auth_headers() -> dict[str, str]:
    """Return Authorization header. Prefer API key, fall back to JWT login."""
    if LITELLM_API_KEY:
        return {"Authorization": f"Bearer {LITELLM_API_KEY}"}
    if LITELLM_USERNAME and LITELLM_PASSWORD:
        token = _jwt_login()
        return {"Authorization": f"Bearer {token}"}
    raise EnvironmentError(
        "No LiteRTLM credentials. Set LITELLM_API_KEY (or LITELLM_USERNAME + LITELLM_PASSWORD) "
        "in services/.env"
    )


def _jwt_login() -> str:
    resp = requests.post(
        f"{LITELLM_BASE_URL}/api/auth/login",
        json={"username": LITELLM_USERNAME, "password": LITELLM_PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"LiteRTLM login failed: {data.get('error')}")
    return data["accessToken"]


# ── Core LLM call ─────────────────────────────────────────────────────────────

def _call_llm(names: list[str], headers: dict[str, str]) -> list[dict[str, Any]]:
    """
    Send a batch of pre-cleaned product names to LiteRTLM via a stateless
    conversation. Returns the parsed JSON array.
    Raises on network or parse errors (caller handles retries).
    """
    conv_name = f"pipeline-norm-{uuid.uuid4().hex[:12]}"
    numbered = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(names))
    prompt = PROMPT_TEMPLATE.format(names=numbered)

    # 1. Create stateless conversation
    resp = requests.post(
        f"{LITELLM_BASE_URL}/api/conversations",
        json={"name": conv_name, "stateless": True, "config": "assistant"},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()

    # 2. Send message (blocking — waits for full reply)
    try:
        resp = requests.post(
            f"{LITELLM_BASE_URL}/api/conversations/{conv_name}/messages",
            json={"message": prompt},
            headers=headers,
            timeout=180,       # large batches on slow models can take ~2 min
        )
        resp.raise_for_status()
        reply: str = resp.json().get("reply", "")
    finally:
        # 3. Always clean up the conversation (fire-and-forget)
        try:
            requests.delete(
                f"{LITELLM_BASE_URL}/api/conversations/{conv_name}",
                headers=headers,
                timeout=10,
            )
        except Exception:
            pass

    # 4. Strip optional markdown code fences (```json ... ```)
    clean = reply.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        # Drop first line (``` or ```json) and last line (```)
        end = -1 if lines[-1].strip() == "```" else len(lines)
        clean = "\n".join(lines[1:end])

    parsed = json.loads(clean)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed).__name__}: {clean[:200]}")
    return parsed


# ── normalized_name derivation ────────────────────────────────────────────────

def _to_ascii_lower(text: str) -> str:
    """Unicode → ASCII → lowercase."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower()


def _derive_normalized_name(item: dict[str, Any]) -> str:
    """
    Build normalized_name from LLM-structured fields:
      "<brand> <model> <spec_value> ..."
    All lowercase ASCII, collapsed whitespace. Max 100 chars.
    Used as the dedup key in Typesense.
    """
    parts: list[str] = []

    brand = item.get("brand") or ""
    model = item.get("model") or ""
    specs = item.get("specs") or []

    if brand:
        parts.append(_to_ascii_lower(brand))
    if model:
        # Compact model codes: remove spaces between letters and digits
        m = _to_ascii_lower(model)
        m = re.sub(r"(?<=[a-z])\s+(?=[0-9])", "", m)
        m = re.sub(r"(?<=[0-9])\s+(?=[a-z])", "", m)
        parts.append(m)

    # Append spec values in a stable order (ram first, then rom/storage, then rest)
    spec_order = ["ram", "rom", "storage", "ssd", "hdd"]
    spec_map: dict[str, str] = {}
    other_specs: list[str] = []

    for spec in specs:
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name") or "").lower().strip()
        value = str(spec.get("value") or "").strip()
        if not value:
            continue
        if name in spec_order:
            spec_map[name] = _to_ascii_lower(value)
        else:
            other_specs.append(_to_ascii_lower(value))

    for key in spec_order:
        if key in spec_map:
            parts.append(spec_map[key])
    parts.extend(other_specs)

    normalized = " ".join(p for p in parts if p)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:100]


# ── Result parsing ────────────────────────────────────────────────────────────

def _parse_item(row_id: str, item: Any) -> tuple[str, str, str | None, str | None, list | None, str | None]:
    """
    Parse one LLM result object.
    Returns (row_id, normalized_name, product_type, brand, specs, model).
    Raises ValueError on unrecoverable parse failures.
    """
    if not isinstance(item, dict):
        raise ValueError(f"Item is not a dict: {item!r}")

    product_type = item.get("product_type")
    brand = item.get("brand")
    model = item.get("model")
    specs = item.get("specs")

    # Coerce types
    product_type = str(product_type).strip().lower() if product_type else None
    brand = str(brand).strip() if brand else None
    model = str(model).strip() if model else None

    # Validate / normalise specs array
    if specs is None:
        specs = []
    elif not isinstance(specs, list):
        specs = []
    else:
        # Keep only valid {name, value} dicts
        specs = [
            {"name": str(s.get("name", "")).strip(), "value": str(s.get("value", "")).strip()}
            for s in specs
            if isinstance(s, dict) and s.get("name") and s.get("value")
        ]

    normalized_name = _derive_normalized_name(item)
    if not normalized_name:
        raise ValueError("Could not derive normalized_name (brand, model, and specs all empty)")

    return row_id, normalized_name, product_type, brand, specs, model


# ── Main normalization function ───────────────────────────────────────────────

def normalize_pending(staging_conn) -> None:
    """
    Fetch all pending rows from staging.raw_crawl, normalize via LLM,
    write structured results to staging.normalized_products.
    """
    headers = _get_auth_headers()

    with staging_conn.cursor() as cur:
        cur.execute(
            "SELECT id, raw_name FROM staging.raw_crawl "
            "WHERE llm_status = 'pending' ORDER BY ingested_at"
        )
        pending_rows = cur.fetchall()

    if not pending_rows:
        print("[llm] No pending rows to normalize.")
        return

    print(f"[llm] {len(pending_rows)} pending rows to normalize (batch size={LLM_BATCH_SIZE}).")
    total_done = 0
    total_failed = 0

    for batch_start in range(0, len(pending_rows), LLM_BATCH_SIZE):
        batch = pending_rows[batch_start : batch_start + LLM_BATCH_SIZE]
        row_ids = [str(r[0]) for r in batch]
        raw_names = [str(r[1]) for r in batch]

        # Pre-clean with ProductNormalizer to reduce prompt noise
        pre_cleaned = [_normalizer.normalize(n) or n for n in raw_names]

        results: list[dict[str, Any]] | None = None
        last_error: Exception | None = None

        for attempt in range(1, LLM_MAX_RETRIES + 1):
            try:
                results = _call_llm(pre_cleaned, headers)
                break
            except Exception as exc:
                last_error = exc
                wait = 2 ** attempt
                print(f"[llm] Attempt {attempt}/{LLM_MAX_RETRIES} failed: {exc}. Retrying in {wait}s...")
                time.sleep(wait)

        batch_num = batch_start // LLM_BATCH_SIZE + 1

        if results is None:
            print(f"[llm] Batch {batch_num}: all retries exhausted — {last_error}")
            _mark_status(staging_conn, row_ids, "failed")
            total_failed += len(batch)
            continue

        if len(results) != len(batch):
            print(
                f"[llm] Batch {batch_num}: response length mismatch "
                f"(expected {len(batch)}, got {len(results)}). Marking all as failed."
            )
            _mark_status(staging_conn, row_ids, "failed")
            total_failed += len(batch)
            continue

        # Parse and write results
        done_ids: list[str] = []
        failed_ids: list[str] = []
        insert_rows: list[tuple] = []

        for row_id, item in zip(row_ids, results):
            try:
                _, normalized_name, product_type, brand, specs, model = _parse_item(row_id, item)
                insert_rows.append((
                    row_id,
                    normalized_name,
                    brand,
                    product_type,
                    model,
                    json.dumps(specs, ensure_ascii=False) if specs is not None else "[]",
                    product_type,   # also used as category for backward compat
                    None,           # llm_model (not available from response)
                ))
                done_ids.append(row_id)
            except Exception as exc:
                print(f"[llm] Row {row_id}: parse error — {exc}")
                failed_ids.append(row_id)

        with staging_conn.cursor() as cur:
            if insert_rows:
                cur.executemany(
                    """
                    INSERT INTO staging.normalized_products
                        (raw_id, normalized_name, brand, product_type, model, specs, category, llm_model)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                    ON CONFLICT (raw_id) DO UPDATE SET
                        normalized_name = EXCLUDED.normalized_name,
                        brand           = EXCLUDED.brand,
                        product_type    = EXCLUDED.product_type,
                        model           = EXCLUDED.model,
                        specs           = EXCLUDED.specs,
                        category        = EXCLUDED.category,
                        llm_model       = EXCLUDED.llm_model,
                        normalized_at   = now()
                    """,
                    insert_rows,
                )
            if done_ids:
                cur.execute(
                    "UPDATE staging.raw_crawl SET llm_status = 'done' "
                    "WHERE id = ANY(%s::uuid[])",
                    (done_ids,),
                )
            if failed_ids:
                cur.execute(
                    "UPDATE staging.raw_crawl SET llm_status = 'failed' "
                    "WHERE id = ANY(%s::uuid[])",
                    (failed_ids,),
                )

        staging_conn.commit()
        total_done += len(done_ids)
        total_failed += len(failed_ids)
        print(f"[llm] Batch {batch_num}: {len(done_ids)} done, {len(failed_ids)} failed.")

    print(f"[llm] Done. Total: {total_done} normalized, {total_failed} failed.")


def _mark_status(conn, row_ids: list[str], status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE staging.raw_crawl SET llm_status = %s WHERE id = ANY(%s::uuid[])",
            (status, row_ids),
        )
    conn.commit()
