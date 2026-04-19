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


def _to_numeric(value: Any) -> Any:
    """Return value only if it parses as a number, else None.
    Prevents header-repeat rows from passing a column name as a numeric value."""
    v = _empty_to_none(value)
    if v is None:
        return None
    try:
        float(v)
        return v
    except (TypeError, ValueError):
        return None


def _is_header_row(row: dict[str, str]) -> bool:
    """Return True if this row is a repeated CSV header (raw_name == 'raw_name')."""
    return (row.get("raw_name") or "").strip().lower() == "raw_name"


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Read a CSV file into rows plus header fieldnames."""
    rows: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [name for name in (reader.fieldnames or []) if name]
        for row in reader:
            rows.append(row)
    return rows, fieldnames


def load_csvs_to_staging(staging_conn) -> None:
    """
    Read all configured CSVs and insert into staging.raw_product.
    """
    total_inserted = 0

    for platform_csv, platform_id in CSV_FILES:
        if not Path(platform_csv).exists():
            print(f"[loader] Skipping {platform_csv.name} — file not found.")
            continue

        source_name = platform_csv.name
        rows = []

        platform_rows, platform_fields = _read_csv(platform_csv)
        is_raw_crawler_csv = "current_price" in platform_fields

        for row in platform_rows:
            raw_name = (row.get("raw_name") or "").strip()
            if not raw_name:
                continue

            # Skip repeated header rows written by crawlers on each save
            if _is_header_row(row):
                continue

            if is_raw_crawler_csv:
                rows.append({
                    "platform_id": platform_id,
                    "raw_name": raw_name,
                    "url": _empty_to_none(row.get("url")),
                    "current_price": _to_numeric(row.get("current_price")),
                    "original_price": _to_numeric(row.get("original_price")),
                    "category": _empty_to_none(row.get("category")),
                    "main_image_url": _empty_to_none(row.get("main_image_url")),
                    "crawled_at": _empty_to_none(row.get("crawled_at")),
                })
                continue

            # Legacy CSV format fallback
            rows.append({
                "platform_id": platform_id,
                "raw_name": raw_name,
                "url": _empty_to_none(row.get("url")),
                "current_price": _to_numeric(row.get("current_price")),
                "original_price": _to_numeric(row.get("original_price")),
                "category": _empty_to_none(row.get("category")),
                "main_image_url": _empty_to_none(row.get("main_image_url")),
                "crawled_at": _empty_to_none(row.get("last_crawled_at")),
            })

        if not rows:
            print(f"[loader] {source_name}: no valid rows found.")
            continue

        insert_sql = """
            INSERT INTO staging.raw_product (
                platform_id, raw_name, url, current_price, original_price,
                category, main_image_url, crawled_at
            ) VALUES %s
        """

        inserted = 0

        with staging_conn.cursor() as cur:
            for i in range(0, len(rows), DB_BATCH_SIZE):
                batch_rows = rows[i : i + DB_BATCH_SIZE]
                values = []
                for row in batch_rows:
                    values.append((
                        row["platform_id"],
                        row["raw_name"],
                        row["url"],
                        row["current_price"],
                        row["original_price"],
                        row["category"],
                        row["main_image_url"],
                        row["crawled_at"],
                    ))
                psycopg2.extras.execute_values(cur, insert_sql, values)
                inserted += len(values)

        staging_conn.commit()
        print(f"[loader] {source_name}: {inserted} inserted.")
        total_inserted += inserted

    print(f"[loader] Done. Total: {total_inserted} inserted.")


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes"}:
        return True
    if s in {"false", "0", "no"}:
        return False
    return None
