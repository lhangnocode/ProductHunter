"""
Stage 1 — Extract → Bronze (staging.raw_crawl)

Reads crawler CSV output files and upserts them into staging.raw_crawl.
Idempotent: re-running only resets llm_status='pending' for rows whose
raw_name changed (i.e. the product was renamed on the platform).
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import psycopg2.extras

from services.pipeline.config import CSV_FILES, DB_BATCH_SIZE


def _empty_to_none(value: Any) -> Any:
    """Convert empty strings and NaN-like values to None for psycopg2."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"nan", "nat", "none", "null"}:
        return None
    try:
        if math.isnan(float(s)):
            return None
    except (TypeError, ValueError):
        pass
    return s


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dicts using stdlib csv (no pandas needed)."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_csvs_to_staging(staging_conn) -> None:
    """
    Read all configured CSV pairs and upsert into staging.raw_crawl.
    """
    total_inserted = 0
    total_updated = 0

    for products_csv, platform_csv, platform_id in CSV_FILES:
        if not Path(platform_csv).exists():
            print(f"[loader] Skipping {platform_csv.name} — file not found.")
            continue

        # Build a slug → main_image_url lookup from products CSV (best-effort)
        image_map: dict[str, str] = {}
        if Path(products_csv).exists():
            for row in _read_csv(products_csv):
                slug = (row.get("slug") or "").strip()
                img = (row.get("main_image_url") or "").strip()
                if slug and img:
                    image_map[slug] = img
        else:
            print(f"[loader] Note: {products_csv.name} not found — image_url lookup skipped.")

        source_name = platform_csv.name
        rows = []

        for row in _read_csv(platform_csv):
            original_item_id = (row.get("original_item_id") or "").strip()
            raw_name = (row.get("raw_name") or "").strip()
            if not original_item_id or not raw_name:
                continue

            main_image_url = image_map.get(original_item_id) or None

            rows.append((
                source_name,
                platform_id,
                raw_name,
                original_item_id,
                _empty_to_none(row.get("url")),
                _empty_to_none(row.get("affiliate_url")),
                _empty_to_none(row.get("current_price")),
                _empty_to_none(row.get("original_price")),
                _to_bool(row.get("in_stock")),
                _empty_to_none(row.get("last_crawled_at")),
                main_image_url,
            ))

        if not rows:
            print(f"[loader] {source_name}: no valid rows found.")
            continue

        upsert_sql = """
            INSERT INTO staging.raw_crawl (
                source_file, platform_id, raw_name, original_item_id,
                url, affiliate_url, current_price, original_price,
                in_stock, last_crawled_at, main_image_url
            ) VALUES %s
            ON CONFLICT (platform_id, original_item_id) DO UPDATE SET
                source_file      = EXCLUDED.source_file,
                raw_name         = EXCLUDED.raw_name,
                current_price    = EXCLUDED.current_price,
                original_price   = EXCLUDED.original_price,
                in_stock         = EXCLUDED.in_stock,
                main_image_url   = COALESCE(EXCLUDED.main_image_url, staging.raw_crawl.main_image_url),
                last_crawled_at  = EXCLUDED.last_crawled_at,
                llm_status       = CASE
                    WHEN staging.raw_crawl.raw_name IS DISTINCT FROM EXCLUDED.raw_name THEN 'pending'
                    ELSE staging.raw_crawl.llm_status
                END
        """

        inserted = 0
        updated = 0

        with staging_conn.cursor() as cur:
            for i in range(0, len(rows), DB_BATCH_SIZE):
                batch = rows[i : i + DB_BATCH_SIZE]
                before_count = _row_count(cur, "staging.raw_crawl")
                psycopg2.extras.execute_values(cur, upsert_sql, batch)
                after_count = _row_count(cur, "staging.raw_crawl")
                batch_inserted = after_count - before_count
                batch_updated = len(batch) - batch_inserted
                inserted += batch_inserted
                updated += batch_updated

        staging_conn.commit()
        print(f"[loader] {source_name}: {inserted} inserted, {updated} updated.")
        total_inserted += inserted
        total_updated += updated

    print(f"[loader] Done. Total: {total_inserted} inserted, {total_updated} updated.")


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes"}:
        return True
    if s in {"false", "0", "no"}:
        return False
    return None


def _row_count(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    result = cur.fetchone()
    return result[0] if result else 0
