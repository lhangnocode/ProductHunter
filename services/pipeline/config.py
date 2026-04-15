"""
Pipeline configuration.
Reads from services/.env (same file used by the crawler).
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_env() -> None:
    """Load services/.env into os.environ (does not overwrite already-set vars)."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

# ── Server DB (existing producthunt DB) ──────────────────────────────────────
# Prefer an explicit SERVER_DB_URL env var. Falls back to building from
# POSTGRES_* parts — but POSTGRES_DB may point to the staging DB in some
# .env setups, so always prefer SERVER_DB_URL when both DBs share the same host.
def _build_server_db_url() -> str:
    url = os.getenv("SERVER_DB_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if url:
        return url
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    # Use SERVER_POSTGRES_DB if set, otherwise fall back to POSTGRES_DB
    db = os.getenv("SERVER_POSTGRES_DB") or os.getenv("POSTGRES_DB", "producthunter")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"


SERVER_DB_URL: str = _build_server_db_url()

# ── Staging DB (separate database, same Postgres instance) ───────────────────
STAGING_DB_URL: str = os.getenv("STAGING_DB_URL", "")
if not STAGING_DB_URL:
    raise EnvironmentError(
        "STAGING_DB_URL is not set. Add it to services/.env.\n"
        "Example: STAGING_DB_URL=postgresql://user:pass@host:5432/producthunter_staging"
    )

# ── LiteRTLM gateway ─────────────────────────────────────────────────────────
LITELLM_BASE_URL: str = os.getenv("LITELLM_BASE_URL", "http://localhost:8080").rstrip("/")
LITELLM_API_KEY: str = os.getenv("LITELLM_API_KEY", "")
LITELLM_USERNAME: str = os.getenv("LITELLM_USERNAME", "")
LITELLM_PASSWORD: str = os.getenv("LITELLM_PASSWORD", "")

# ── Typesense (reused from crawler env) ──────────────────────────────────────
TYPESENSE_API_KEY: str = os.getenv("TYPESENSE_API_KEY", "")
TYPESENSE_HOST: str = os.getenv("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT: str = os.getenv("TYPESENSE_PORT", "8108")
TYPESENSE_PROTOCOL: str = os.getenv("TYPESENSE_PROTOCOL", "http")

# ── Pipeline tuning ───────────────────────────────────────────────────────────
LLM_BATCH_SIZE: int = int(os.getenv("LLM_BATCH_SIZE", "10"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
DEDUP_SCORE_THRESHOLD: float = float(os.getenv("DEDUP_SCORE_THRESHOLD", "0.85"))
DB_BATCH_SIZE: int = 200

# ── Crawler CSV output directory ─────────────────────────────────────────────
CRAWLER_OUTPUT_DIR: Path = Path(__file__).resolve().parents[1] / "crawler" / "output"

# ── CSV file registry ─────────────────────────────────────────────────────────
# Each entry: (platform_products_csv, platform_id)
CSV_FILES: list[tuple[Path, int]] = [
    (CRAWLER_OUTPUT_DIR / "fptshop_products.csv", 7),
    (CRAWLER_OUTPUT_DIR / "phongvu_products.csv", 8),
    (CRAWLER_OUTPUT_DIR / "cellphones_products.csv", 9),
]
