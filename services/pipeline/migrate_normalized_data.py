"""
Migrate data from staging to server DB.

Flow:
1) Read staging.raw_product + staging.normalized_product
2) Upsert products
3) Upsert platform_products
4) Insert price_records
5) Sync Typesense
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Iterable
import unicodedata
from urllib.parse import urlparse

import psycopg2.extras

from services.crawler.core.storage.typesense_handler import TypesenseHandler
from services.pipeline.config import (
    DB_BATCH_SIZE,
    TYPESENSE_API_KEY,
    TYPESENSE_HOST,
    TYPESENSE_PORT,
    TYPESENSE_PROTOCOL,
)
from services.pipeline.db import get_server_conn, get_staging_conn


@dataclass
class StagingRecord:
    raw_id: str
    platform_id: int
    raw_name: str
    url: str | None
    current_price: Decimal | None
    original_price: Decimal | None
    category: str | None
    main_image_url: str | None
    crawled_at: str | None
    normalized_name: str
    product_name: str
    brand: str | None
    model: str | None
    manufacture_model_id: str | None
    specs: dict | None


def _slug_from_url(url: str | None) -> str | None:
    if not url:
        return None
    path = urlparse(url).path.rstrip("/")
    if not path:
        return None
    return path.split("/")[-1] or None


def _slugify(text: str) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFKD", text)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def _fetch_staging_records(staging_conn) -> list[StagingRecord]:
    with staging_conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                rp.id,
                rp.platform_id,
                rp.raw_name,
                rp.url,
                rp.current_price,
                rp.original_price,
                rp.category,
                rp.main_image_url,
                rp.crawled_at,
                np.normalized_name,
                np.product_name,
                np.brand,
                np.model,
                np.manufacture_model_id,
                np.specs
            FROM staging.raw_product rp
            JOIN staging.normalized_product np ON np.raw_id = rp.id
            WHERE rp.llm_status = 'done'
            ORDER BY rp.ingested_at
            """
        )
        rows = cur.fetchall()

    records: list[StagingRecord] = []
    for row in rows:
        (
            raw_id,
            platform_id,
            raw_name,
            url,
            current_price,
            original_price,
            category,
            main_image_url,
            crawled_at,
            normalized_name,
            product_name,
            brand,
            model,
            manufacture_model_id,
            specs,
        ) = row
        records.append(
            StagingRecord(
                raw_id=str(raw_id),
                platform_id=int(platform_id),
                raw_name=str(raw_name),
                url=str(url) if url else None,
                current_price=Decimal(str(current_price)) if current_price is not None else None,
                original_price=Decimal(str(original_price)) if original_price is not None else None,
                category=str(category) if category else None,
                main_image_url=str(main_image_url) if main_image_url else None,
                crawled_at=str(crawled_at) if crawled_at else None,
                normalized_name=str(normalized_name),
                product_name=str(product_name),
                brand=str(brand) if brand else None,
                model=str(model) if model else None,
                manufacture_model_id=str(manufacture_model_id) if manufacture_model_id else None,
                specs=specs if isinstance(specs, dict) else None,
            )
        )
    return records


def _upsert_products(server_conn, records: Iterable[StagingRecord]) -> tuple[dict[str, str], int, int]:
    sql = """
        INSERT INTO products (normalized_name, product_name, brand, category, main_image_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (product_name) DO UPDATE SET
            normalized_name = EXCLUDED.normalized_name,
            brand           = EXCLUDED.brand,
            category        = EXCLUDED.category,
            main_image_url  = COALESCE(EXCLUDED.main_image_url, products.main_image_url)
        RETURNING id, product_name, (xmax = 0) AS inserted
    """

    seen: dict[str, StagingRecord] = {}
    for r in records:
        if r.product_name:
            seen[r.product_name] = r

    product_ids: dict[str, str] = {}
    inserted = 0
    updated = 0
    with server_conn.cursor() as cur:
        for r in seen.values():
            cur.execute(
                sql,
                (
                    r.normalized_name,
                    r.product_name,
                    r.brand,
                    r.category,
                    r.main_image_url,
                ),
            )
            row = cur.fetchone()
            if row:
                product_ids[str(row[1])] = str(row[0])
                if row[2]:
                    inserted += 1
                else:
                    updated += 1
    server_conn.commit()
    return product_ids, inserted, updated


def _upsert_platform_products(
    server_conn,
    records: Iterable[StagingRecord],
    product_ids: dict[str, str],
) -> tuple[list[tuple[str, Decimal | None, Decimal | None]], int, int]:
    sql = """
        INSERT INTO platform_products (
            product_id, platform_id, raw_name, original_item_id,
            url, affiliate_url, current_price, original_price,
            in_stock, last_crawled_at
        ) VALUES %s
        ON CONFLICT (platform_id, original_item_id) DO UPDATE SET
            product_id      = EXCLUDED.product_id,
            raw_name        = EXCLUDED.raw_name,
            url             = EXCLUDED.url,
            affiliate_url   = EXCLUDED.affiliate_url,
            current_price   = EXCLUDED.current_price,
            original_price  = EXCLUDED.original_price,
            in_stock        = EXCLUDED.in_stock,
            last_crawled_at = EXCLUDED.last_crawled_at
        RETURNING id, current_price, original_price, (xmax = 0) AS inserted
    """

    deduped: dict[tuple[int, str], tuple] = {}
    for r in records:
        product_id = product_ids.get(r.product_name)
        if not product_id:
            continue
        original_item_id = _slug_from_url(r.url)
        if not original_item_id:
            original_item_id = _slugify(r.product_name) or _slugify(r.raw_name)
        if not original_item_id:
            continue
        key = (r.platform_id, original_item_id)
        deduped[key] = (
            product_id,
            r.platform_id,
            r.raw_name,
            original_item_id,
            r.url,
            None,               # affiliate_url
            r.current_price,
            r.original_price,
            True if r.current_price is not None else None,
            r.crawled_at,
        )

    rows = list(deduped.values())
    results: list[tuple[str, Decimal | None, Decimal | None]] = []
    inserted = 0
    updated = 0
    with server_conn.cursor() as cur:
        for i in range(0, len(rows), DB_BATCH_SIZE):
            batch = rows[i : i + DB_BATCH_SIZE]
            batch_results = psycopg2.extras.execute_values(cur, sql, batch, fetch=True)
            for row in batch_results:
                results.append((row[0], row[1], row[2]))
                if row[3]:
                    inserted += 1
                else:
                    updated += 1
    server_conn.commit()
    return results, inserted, updated


def _insert_price_records(server_conn, platform_product_info: list[tuple[str, Decimal | None, Decimal | None]]) -> None:
    sql = """
        INSERT INTO price_records (
            platform_product_id, price, original_price, is_flash_sale, recorded_at
        ) VALUES %s
    """
    rows = [
        (info[0], info[1], info[2], False, "now()")
        for info in platform_product_info
        if info[1] is not None  # only save if current_price exists
    ]
    if not rows:
        return
    with server_conn.cursor() as cur:
        for i in range(0, len(rows), DB_BATCH_SIZE):
            batch = rows[i : i + DB_BATCH_SIZE]
            psycopg2.extras.execute_values(cur, sql, batch)
    server_conn.commit()


def _sync_typesense(records: Iterable[StagingRecord], product_ids: dict[str, str]) -> None:
    typesense = TypesenseHandler(
        api_key=TYPESENSE_API_KEY,
        host=TYPESENSE_HOST,
        port=TYPESENSE_PORT,
        protocol=TYPESENSE_PROTOCOL,
    )
    try:
        typesense.ensure_collection()
    except Exception as exc:
        print(f"[typesense] Unavailable: {exc}")
        return

    documents = []
    for r in records:
        product_id = product_ids.get(r.product_name)
        if not product_id:
            continue
        documents.append({
            "id": product_id,
            "normalized_name": r.normalized_name,
            "product_name": r.product_name,
        })

    if not documents:
        return
    try:
        typesense.import_documents("products", documents)
    except Exception as exc:
        print(f"[typesense] Import failed: {exc}")


def main() -> None:
    staging_conn = get_staging_conn()
    server_conn = get_server_conn()
    try:
        records = _fetch_staging_records(staging_conn)
        if not records:
            print("[migrate] No normalized staging records to migrate.")
            return

        product_ids, products_inserted, products_updated = _upsert_products(server_conn, records)
        platform_info, platform_inserted, platform_updated = _upsert_platform_products(server_conn, records, product_ids)
        _insert_price_records(server_conn, platform_info)
        _sync_typesense(records, product_ids)
        print(
            "[migrate] Done. "
            f"products={len(product_ids)} (inserted={products_inserted}, updated={products_updated}) "
            f"platform_products={len(platform_info)} (inserted={platform_inserted}, updated={platform_updated})"
        )
    finally:
        staging_conn.close()
        server_conn.close()


if __name__ == "__main__":
    main()
