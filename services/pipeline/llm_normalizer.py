"""
Stage 2 — Transform via LiteRTLM (staging.raw_product → staging.normalized_product)

For each row in staging.raw_product with llm_status='pending':
  1. Pre-clean raw_name with ProductNormalizer (reduce noise in prompt)
  2. Batch N names into one LiteRTLM stateless conversation request
  3. Parse structured JSON response:
       { product_type, brand, model, specs: [{name, value}, ...], manufacture_model_id }
  4. Build normalized_name in code from structured fields
  5. Write results to staging.normalized_product
  6. Mark llm_status='done' on success, 'failed' on parse error

normalized_name derivation:
  "<category> <brand> <model>" → lowercased, ASCII-safe
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
from services.pipeline.define.instruction import LLM_INSTRUCTION


_normalizer = ProductNormalizer()
print(LLM_INSTRUCTION)

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
    prompt = numbered

    # 1. Send message (blocking — waits for full reply)
    reply = ""
    try:
        resp = requests.post(
            f"{LITELLM_BASE_URL}/api/conversations/data-normalizer/messages",
            json={"message": prompt},
            headers=headers,
            timeout=180,       # large batches on slow models can take ~2 min
        )
        resp.raise_for_status()
        reply = resp.json().get("reply", "")
    except Exception as exc:
        print(f"[llm] Error during LLM call: {exc}")
        pass  # will be handled by caller's retry logic

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


def _to_ascii_lower(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower()


def _derive_normalized_name(
    category: str | None,
    brand: str | None,
    model: str | None,
) -> str:
    parts: list[str] = []

    if category:
        parts.append(_to_ascii_lower(category))
    if brand:
        parts.append(_to_ascii_lower(brand))
    if model:
        m = _to_ascii_lower(model)
        m = re.sub(r"(?<=[a-z])\s+(?=[0-9])", "", m)
        m = re.sub(r"(?<=[0-9])\s+(?=[a-z])", "", m)
        parts.append(m)

    normalized = " ".join(p for p in parts if p)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:100]


def _derive_product_name(
    category: str | None,
    brand: str | None,
    model: str | None,
) -> str:
    parts: list[str] = []
    if category:
        parts.append(category.strip())
    if brand:
        parts.append(brand.strip())
    if model:
        parts.append(model.strip())
    return " ".join(p for p in parts if p).strip()[:150]


# ── Result parsing ────────────────────────────────────────────────────────────

def _parse_item(
    row_id: str,
    item: Any,
) -> tuple[str, str, str, str | None, str | None, list | None, str | None, str | None]:
    """
    Parse one LLM result object.
    Returns (row_id, normalized_name, product_name, category, brand, specs, model, manufacture_model_id).
    Raises ValueError on unrecoverable parse failures.
    """
    if not isinstance(item, dict):
        raise ValueError(f"Item is not a dict: {item!r}")

    product_type = item.get("product_type")
    category = item.get("category")
    brand = item.get("brand")
    model = item.get("model")
    manufacture_model_id = item.get("manufacture_model_id")
    specs = item.get("specs")

    # Coerce types
    if not product_type and category:
        product_type = category
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

    normalized_name = _derive_normalized_name(product_type, brand, model)
    product_name = _derive_product_name(product_type, brand, model)
    if not normalized_name:
        raise ValueError("Could not derive normalized_name (brand/model/specs empty)")

    return (
        row_id,
        normalized_name,
        product_name,
        product_type,
        brand,
        specs,
        model,
        str(manufacture_model_id).strip().upper() if manufacture_model_id else None,
    )


def normalize_names(raw_names: list[str]) -> list[dict[str, str | None]]:
    """
    Normalize a list of raw names via LLM.
    Returns list of {normalized_name, category} aligned with input order.
    """
    if not raw_names:
        return []

    headers = _get_auth_headers()
    results_all: list[dict[str, str | None]] = []

    for batch_start in range(0, len(raw_names), LLM_BATCH_SIZE):
        batch = raw_names[batch_start : batch_start + LLM_BATCH_SIZE]
        pre_cleaned = [_normalizer.normalize(n) or n for n in batch]

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

        if results is None:
            raise RuntimeError(f"LLM failed for batch starting {batch_start}: {last_error}")

        print(f"[llm] Batch {batch_start // LLM_BATCH_SIZE + 1}: received {len(results)} results for {len(batch)} names.")
        print(f"[llm] Sample result: {results[0] if results else 'None'}")
        print(f"[llm] Sample raw name: {batch[0]}")
        
        
        if len(results) != len(batch):
            raise ValueError(
                f"LLM response length mismatch (expected {len(batch)}, got {len(results)})"
            )

        for item in results:
            try:
                _, normalized_name, product_name, product_type, _, _, _, manufacture_model_id = _parse_item("", item)
                results_all.append({
                    "normalized_name": normalized_name,
                    "product_name": product_name,
                    "category": product_type,
                    "manufacture_model_id": manufacture_model_id,
                })
            except Exception as exc:
                print(f"[llm] Parse error: {exc}")
                results_all.append({
                    "normalized_name": None,
                    "product_name": None,
                    "category": None,
                    "manufacture_model_id": None,
                })

    return results_all


# ── Main normalization function ───────────────────────────────────────────────

def normalize_pending(staging_conn) -> None:
    """
    Fetch all pending rows from staging.raw_product, normalize via LLM,
    write structured results to staging.normalized_product.
    """
    headers = _get_auth_headers()

    with staging_conn.cursor() as cur:
        cur.execute(
            "SELECT id, raw_name FROM staging.raw_product "
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
                _, normalized_name, product_name, product_type, brand, specs, model, manufacture_model_id = _parse_item(row_id, item)
                insert_rows.append((
                    row_id,
                    normalized_name,
                    product_name,
                    brand,
                    model,
                    manufacture_model_id,
                    product_type,
                    json.dumps(specs, ensure_ascii=False) if specs is not None else "[]",
                ))
                done_ids.append(row_id)
            except Exception as exc:
                print(f"[llm] Row {row_id}: parse error — {exc}")
                failed_ids.append(row_id)

        with staging_conn.cursor() as cur:
            if insert_rows:
                cur.executemany(
                    """
                    INSERT INTO staging.normalized_product
                        (raw_id, normalized_name, product_name, brand, model, manufacture_model_id, category, specs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (raw_id) DO UPDATE SET
                        normalized_name      = EXCLUDED.normalized_name,
                        product_name         = EXCLUDED.product_name,
                        brand                = EXCLUDED.brand,
                        model                = EXCLUDED.model,
                        manufacture_model_id = EXCLUDED.manufacture_model_id,
                        category             = EXCLUDED.category,
                        specs                = EXCLUDED.specs,
                        normalized_at        = now()
                """,
                insert_rows,
            )
            if done_ids:
                cur.execute(
                    "UPDATE staging.raw_product SET llm_status = 'done' "
                    "WHERE id = ANY(%s::uuid[])",
                    (done_ids,),
                )
            if failed_ids:
                cur.execute(
                    "UPDATE staging.raw_product SET llm_status = 'failed' "
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
            "UPDATE staging.raw_product SET llm_status = %s WHERE id = ANY(%s::uuid[])",
            (status, row_ids),
        )
    conn.commit()
