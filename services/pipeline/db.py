"""
Database connection helpers for the pipeline.
Two separate Postgres connections:
  - staging_conn  → producthunter_staging (bronze/silver layers)
  - server_conn   → producthunter (gold / production tables)
"""
from __future__ import annotations

import psycopg2
import psycopg2.extras

from services.pipeline.config import STAGING_DB_URL, SERVER_DB_URL


def get_staging_conn():
    """Open a psycopg2 connection to the staging database."""
    conn = psycopg2.connect(STAGING_DB_URL)
    conn.autocommit = False
    return conn


def get_server_conn():
    """Open a psycopg2 connection to the production server database."""
    conn = psycopg2.connect(SERVER_DB_URL)
    conn.autocommit = False
    return conn


def ensure_staging_schema(conn) -> None:
    """
    Create the staging schema and raw/normalized tables if they don't exist.
    Idempotent — safe to call on every pipeline run.
    """
    ddl = """
    CREATE SCHEMA IF NOT EXISTS staging;

    CREATE TABLE IF NOT EXISTS staging.raw_product (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        platform_id     INT,
        raw_name        TEXT,
        url             TEXT,
        price           NUMERIC,
        category        TEXT,
        main_image_url  TEXT,
        crawled_at      TIMESTAMPTZ,
        ingested_at     TIMESTAMPTZ DEFAULT now(),
        llm_status      TEXT NOT NULL DEFAULT 'pending'
    );

    CREATE TABLE IF NOT EXISTS staging.normalized_product (
        raw_id               UUID PRIMARY KEY REFERENCES staging.raw_product(id) ON DELETE CASCADE,
        normalized_name      TEXT,
        product_name         TEXT,
        brand                TEXT,
        model                TEXT,
        manufacture_model_id TEXT,
        category             TEXT,
        specs                JSONB,
        normalized_at        TIMESTAMPTZ DEFAULT now()
    );
    """

    migrations = [
        "ALTER TABLE staging.raw_product ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ DEFAULT now()",
        "ALTER TABLE staging.raw_product ADD COLUMN IF NOT EXISTS llm_status TEXT NOT NULL DEFAULT 'pending'",
        "ALTER TABLE staging.normalized_product ADD COLUMN IF NOT EXISTS product_name TEXT",
        "ALTER TABLE staging.normalized_product DROP COLUMN IF EXISTS mapping_name",
    ]

    with conn.cursor() as cur:
        cur.execute(ddl)
        for migration in migrations:
            cur.execute(migration)
    conn.commit()
    print("[db] Staging schema ensured.")


def ensure_server_schema(conn) -> None:
    """
    Apply additive adjustments to the server schema required by the pipeline.
    """
    ddl = """
    ALTER TABLE platform_products
    ALTER COLUMN url DROP NOT NULL;

    ALTER TABLE products
    ADD COLUMN IF NOT EXISTS slug TEXT;

    ALTER TABLE products
    ALTER COLUMN slug DROP NOT NULL;

    ALTER TABLE products
    ADD COLUMN IF NOT EXISTS product_name TEXT;

    CREATE UNIQUE INDEX IF NOT EXISTS uq_products_product_name ON products (product_name);
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("[db] Server schema ensured.")
