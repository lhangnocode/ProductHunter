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
    Create the staging schema and its two tables if they don't exist.
    Also applies any additive column migrations for existing tables.
    Idempotent — safe to call on every pipeline run.
    """
    ddl = """
    CREATE SCHEMA IF NOT EXISTS staging;

    CREATE TABLE IF NOT EXISTS staging.raw_crawl (
        id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        source_file      TEXT NOT NULL,
        platform_id      INT  NOT NULL,
        raw_name         TEXT NOT NULL,
        original_item_id TEXT NOT NULL,
        url              TEXT,
        affiliate_url    TEXT,
        current_price    NUMERIC,
        original_price   NUMERIC,
        in_stock         BOOLEAN,
        main_image_url   TEXT,
        last_crawled_at  TIMESTAMPTZ,
        ingested_at      TIMESTAMPTZ DEFAULT now(),
        llm_status       TEXT NOT NULL DEFAULT 'pending',
        UNIQUE (platform_id, original_item_id)
    );

    CREATE TABLE IF NOT EXISTS staging.normalized_products (
        raw_id           UUID PRIMARY KEY REFERENCES staging.raw_crawl(id) ON DELETE CASCADE,
        normalized_name  TEXT NOT NULL,
        brand            TEXT,
        product_type     TEXT,
        model            TEXT,
        specs            JSONB,
        category         TEXT,
        llm_model        TEXT,
        normalized_at    TIMESTAMPTZ DEFAULT now()
    );
    """

    # Additive migrations: add new columns to normalized_products if the table
    # already exists without them (e.g. from a previous pipeline version).
    migrations = [
        "ALTER TABLE staging.normalized_products ADD COLUMN IF NOT EXISTS product_type TEXT",
        "ALTER TABLE staging.normalized_products ADD COLUMN IF NOT EXISTS model TEXT",
        "ALTER TABLE staging.normalized_products ADD COLUMN IF NOT EXISTS specs JSONB",
    ]

    with conn.cursor() as cur:
        cur.execute(ddl)
        for migration in migrations:
            cur.execute(migration)
    conn.commit()
    print("[db] Staging schema ensured.")
