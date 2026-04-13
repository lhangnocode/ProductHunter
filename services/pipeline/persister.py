"""
Stage 3b — Load into server DB + Typesense

Persists resolved products into the production server database:
  1. Upsert platforms
  2. Insert new products → get their UUIDs
  3. Upsert all platform_products
  4. Sync new/changed products to Typesense
"""
from __future__ import annotations

from typing import Optional

import psycopg2.extras

from services.crawler.core.storage.typesense_handler import TypesenseHandler
from services.pipeline.config import DB_BATCH_SIZE
from services.pipeline.product_resolver import ResolvedProduct


# Platform metadata keyed by platform_id
PLATFORM_META: dict[int, tuple[str, str]] = {
    # platform_id: (name, base_url)
    7: ("FPT Shop",  "https://fptshop.com.vn"),
    8: ("Phong Vũ",  "https://phongvu.vn"),
}


def persist(
    resolved_products: list[ResolvedProduct],
    server_conn,
    typesense: TypesenseHandler,
) -> None:
    """
    Write all resolved products into server DB and sync Typesense.
    """
    if not resolved_products:
        print("[persister] Nothing to persist.")
        return

    # ── 1. Upsert platforms ───────────────────────────────────────────────────
    platform_ids_seen = {r.platform_id for r in resolved_products}
    _upsert_platforms(server_conn, platform_ids_seen)

    # ── 2. Insert new products → resolve their UUIDs ──────────────────────────
    new_products = [r for r in resolved_products if r.is_new]
    if new_products:
        _insert_new_products(server_conn, new_products)

    # Filter out records that still have no product_id after insert (edge case)
    valid = [r for r in resolved_products if r.product_id]
    skipped = len(resolved_products) - len(valid)
    if skipped:
        print(f"[persister] Skipped {skipped} records with no product_id.")

    # ── 3. Upsert platform_products ───────────────────────────────────────────
    _upsert_platform_products(server_conn, valid)

    # ── 4. Typesense sync (only new products) ─────────────────────────────────
    _sync_typesense(typesense, new_products)

    print(f"[persister] Done. {len(valid)} platform_products upserted.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upsert_platforms(conn, platform_ids: set[int]) -> None:
    with conn.cursor() as cur:
        for pid in platform_ids:
            meta = PLATFORM_META.get(pid)
            if not meta:
                continue
            name, base_url = meta
            cur.execute(
                """
                INSERT INTO platforms (id, name, base_url, affiliate_config)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name     = EXCLUDED.name,
                    base_url = EXCLUDED.base_url
                """,
                (pid, name, base_url, None),
            )
    conn.commit()
    print(f"[persister] Platforms upserted: {platform_ids}")


def _insert_new_products(conn, new_products: list[ResolvedProduct]) -> None:
    """
    Insert new products with ON CONFLICT (slug) DO UPDATE.
    Retrieves the generated/existing UUIDs and populates product_id on each record.
    """
    insert_sql = """
        INSERT INTO products (normalized_name, slug, brand, category, main_image_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE SET
            normalized_name = EXCLUDED.normalized_name,
            brand           = EXCLUDED.brand,
            category        = EXCLUDED.category,
            main_image_url  = COALESCE(EXCLUDED.main_image_url, products.main_image_url)
        RETURNING id, slug
    """
    slug_to_id: dict[str, str] = {}

    with conn.cursor() as cur:
        # Deduplicate by slug before inserting
        seen_slugs: dict[str, ResolvedProduct] = {}
        for r in new_products:
            if r.slug:
                seen_slugs[r.slug] = r

        for r in seen_slugs.values():
            cur.execute(insert_sql, (
                r.normalized_name,
                r.slug,
                r.brand,
                r.category,
                r.main_image_url,
            ))
            row = cur.fetchone()
            if row:
                slug_to_id[row[1]] = str(row[0])

    conn.commit()

    # Populate product_id back onto each ResolvedProduct
    for r in new_products:
        if r.slug in slug_to_id:
            r.product_id = slug_to_id[r.slug]

    inserted = len(slug_to_id)
    print(f"[persister] Products inserted/updated: {inserted}")


def _upsert_platform_products(conn, records: list[ResolvedProduct]) -> None:
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
    """
    rows = [
        (
            r.product_id,
            r.platform_id,
            r.raw_name,
            r.original_item_id,
            r.url,
            r.affiliate_url,
            r.current_price,
            r.original_price,
            r.in_stock,
            r.last_crawled_at,
        )
        for r in records
        if r.product_id  # safety guard
    ]

    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), DB_BATCH_SIZE):
            batch = rows[i : i + DB_BATCH_SIZE]
            psycopg2.extras.execute_values(cur, sql, batch)
            total += len(batch)

    conn.commit()
    print(f"[persister] platform_products upserted: {total}")


def _sync_typesense(
    typesense: TypesenseHandler,
    new_products: list[ResolvedProduct],
) -> None:
    """Upsert only new products (those that were just inserted) into Typesense."""
    synced = 0
    errors = 0
    for r in new_products:
        if not r.product_id or not r.normalized_name:
            continue
        try:
            typesense.upsert_document(
                "products",
                {
                    "id": r.product_id,
                    "normalized_name": r.normalized_name,
                    "slug": r.slug,
                },
            )
            synced += 1
        except Exception as exc:
            print(f"[persister] Typesense upsert failed for {r.slug}: {exc}")
            errors += 1

    print(f"[persister] Typesense sync: {synced} upserted, {errors} errors.")
