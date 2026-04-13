"""
Pipeline orchestrator.

Run order:
  1. Ensure staging schema exists
  2. Ensure Typesense collection exists
  3. Stage 1: Load CSVs → staging.raw_crawl (bronze)
  4. Stage 2: LLM normalization → staging.normalized_products (silver)
  5. Stage 3a: Resolve product IDs via Typesense dedup
  6. Stage 3b: Persist into server DB + Typesense (gold)

Usage:
    python -m services.pipeline.main
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime

from services.crawler.core.storage.typesense_handler import TypesenseHandler
from services.pipeline.config import (
    TYPESENSE_API_KEY,
    TYPESENSE_HOST,
    TYPESENSE_PORT,
    TYPESENSE_PROTOCOL,
)
from services.pipeline.db import ensure_staging_schema, get_server_conn, get_staging_conn
from services.pipeline.llm_normalizer import normalize_pending
from services.pipeline.persister import persist
from services.pipeline.product_resolver import resolve_products
from services.pipeline.staging_loader import load_csvs_to_staging


def main() -> None:
    start = datetime.now()
    print(f"\n{'='*60}")
    print(f"[pipeline] START — {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    staging_conn = None
    server_conn = None

    try:
        # ── Connections ───────────────────────────────────────────────────────
        print("[pipeline] Connecting to staging DB...")
        staging_conn = get_staging_conn()

        print("[pipeline] Connecting to server DB...")
        server_conn = get_server_conn()

        typesense = TypesenseHandler(
            api_key=TYPESENSE_API_KEY,
            host=TYPESENSE_HOST,
            port=TYPESENSE_PORT,
            protocol=TYPESENSE_PROTOCOL,
        )

        # ── Schema setup ──────────────────────────────────────────────────────
        print("\n[pipeline] Stage 0: Ensuring schemas...")
        ensure_staging_schema(staging_conn)
        try:
            typesense.ensure_collection()
            print("[pipeline] Typesense collection ensured.")
        except Exception as exc:
            print(f"[pipeline] Warning: Typesense unavailable — {exc}")

        # ── Stage 1: Extract → Bronze ─────────────────────────────────────────
        print("\n[pipeline] Stage 1: Loading CSVs into staging.raw_crawl...")
        load_csvs_to_staging(staging_conn)

        # ── Stage 2: Transform via LLM → Silver ───────────────────────────────
        print("\n[pipeline] Stage 2: LLM normalization...")
        normalize_pending(staging_conn)

        # ── Stage 3a: Resolve product IDs ─────────────────────────────────────
        print("\n[pipeline] Stage 3a: Resolving product IDs via Typesense...")
        resolved = resolve_products(staging_conn, typesense)

        # ── Stage 3b: Persist → Gold ──────────────────────────────────────────
        print("\n[pipeline] Stage 3b: Persisting to server DB + Typesense...")
        persist(resolved, server_conn, typesense)

    except Exception:
        print("\n[pipeline] FATAL ERROR:")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if staging_conn:
            staging_conn.close()
        if server_conn:
            server_conn.close()

    end = datetime.now()
    elapsed = end - start
    print(f"\n{'='*60}")
    print(f"[pipeline] DONE — elapsed {elapsed}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
