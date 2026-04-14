# Technical Architecture: Crawler & ELT Pipeline

## Overview

The `services/` layer has two independent subsystems:

1. **Crawler** — scrapes product listings from e-commerce platforms, outputs raw CSV files.
2. **Pipeline** — reads those CSVs, normalises product names via an LLM, and loads clean data into the production database and search index.

They are deliberately decoupled: the crawler has **no database or Typesense knowledge**. All storage logic lives exclusively in the pipeline.

---

## System Container Diagram

High-level view of every runtime component and how they communicate.

```mermaid
C4Container
    title System Containers — ProductHunter Services

    Person(devops, "Operator / Cron", "Triggers crawler and pipeline on schedule")

    System_Boundary(services, "services/") {

        Container(crawler, "Crawler", "Python · Playwright · BeautifulSoup", "Scrapes FPT Shop and Phong Vũ. Writes raw product data to CSV files.")

        Container(csvstore, "CSV Output", "File system\nservices/crawler/output/", "Intermediate checkpoint.\nfpt_products.csv\nfpt_platform_products.csv\nphongvu_products.csv\nphongvu_platform_products.csv")

        Container(pipeline, "ELT Pipeline", "Python · psycopg2 · requests", "4-stage ELT process:\nLoad CSVs → LLM normalize\n→ Typesense dedup → Persist")
    }

    System_Ext(litellm, "LiteRTLM Gateway", "Self-hosted LLM API\nhttps://rogo.tail47f64f.ts.net\nStateless conversation endpoint")

    System_Boundary(infra, "Infrastructure (remote Postgres instance)") {
        ContainerDb(stagingdb, "Staging DB", "PostgreSQL\nproducthunter_staging", "Bronze layer: staging.raw_crawl\nSilver layer: staging.normalized_products")

        ContainerDb(serverdb, "Server DB", "PostgreSQL\ndb_producthunt", "Gold layer:\nproducts, platform_products,\nplatforms, price_records,\nwish_list, price_alerts")
    }

    ContainerDb(typesense, "Typesense", "Search engine\nport 8108", "products collection\nFuzzy search index for\nproduct name dedup + API search")

    Rel(devops, crawler, "Triggers", "cron / shell")
    Rel(devops, pipeline, "Triggers", "cron / shell")
    Rel(crawler, csvstore, "Writes", "CSV (utf-8-sig)")
    Rel(pipeline, csvstore, "Reads", "csv.DictReader")
    Rel(pipeline, stagingdb, "Reads / Writes", "psycopg2")
    Rel(pipeline, litellm, "POST /api/conversations\n(stateless, batch)", "HTTPS REST")
    Rel(pipeline, typesense, "Search (dedup)\nUpsert (index)", "HTTP REST")
    Rel(pipeline, serverdb, "Upserts\nproducts + platform_products", "psycopg2")
```

---

## Directory Structure

```
services/
├── .env                          # Shared config (both crawler + pipeline)
├── .env.example                  # Template with all required keys
├── crawler/
│   ├── main.py                   # Crawler entry point
│   ├── run_crawler.sh            # Shell wrapper (for cron)
│   ├── core/
│   │   ├── crawler.py            # Abstract base class (scrape-only)
│   │   ├── define/
│   │   │   └── platform_type.py  # Platform ID constants
│   │   └── storage/              # Reusable storage clients (used by pipeline)
│   │       ├── database_handler.py
│   │       ├── storage_manager.py
│   │       ├── typesense_handler.py
│   │       └── models/
│   │           ├── product.py
│   │           └── platform_product.py
│   ├── impl/
│   │   ├── fpt/crawler_fptshop.py     # FPT Shop scraper
│   │   └── phongvu/crawler_phongvu.py # Phong Vũ scraper
│   ├── utils/
│   │   └── text_parser.py        # ProductNormalizer (pre-cleaning utility)
│   └── output/                   # CSV snapshots written after each crawl
│       ├── fpt_products.csv
│       ├── fpt_platform_products.csv
│       ├── phongvu_products.csv
│       └── phongvu_platform_products.csv
└── pipeline/
    ├── main.py                   # Pipeline entry point (orchestrator)
    ├── run_pipeline.sh           # Shell wrapper (for cron)
    ├── config.py                 # All config/env constants
    ├── db.py                     # Postgres connection helpers + staging schema DDL
    ├── staging_loader.py         # Stage 1: CSV → staging.raw_crawl
    ├── llm_normalizer.py         # Stage 2: LLM normalization → staging.normalized_products
    ├── product_resolver.py       # Stage 3a: Typesense dedup → resolve product_id
    └── persister.py              # Stage 3b: Upsert server DB + Typesense sync
```

---

## Crawler Subsystem

### Crawler Component Diagram

Internal structure of the crawler subsystem and data flow out to CSV files.

```mermaid
flowchart TD
    subgraph entry["Crawler Entry Point"]
        MAIN["crawler/main.py\n─────────────\nOrchestrates crawlers\nin sequence"]
    end

    subgraph core["crawler/core/"]
        BASE["crawler.py\n─────────────\nAbstract Crawler\nname, output_dir, base_url\ncrawl() → abstract"]
        PT["define/platform_type.py\n─────────────\nPlatformType constants\nFPTSHOP=7 · PHONGVU=8"]
        NORM["utils/text_parser.py\n─────────────\nProductNormalizer\nUnicode → lowercase\nstrip marketing terms\ncompact model codes"]
    end

    subgraph impl["crawler/impl/"]
        FPT["fpt/crawler_fptshop.py\n─────────────\nFptTrojanPro\nPlaywright + Stealth\n~25 categories\nscroll + Xem thêm loop\nparse cardDefault blocks"]
        PV["phongvu/crawler_phongvu.py\n─────────────\nPhongVuCrawler\nPlaywright + Stealth\n~12 categories\nanchor-climb algorithm\n₫ tag → parent walk"]
    end

    subgraph browser["Browser Automation"]
        PW["Playwright\nHeadless Chromium"]
        BS["BeautifulSoup\nHTML parser"]
    end

    subgraph output["crawler/output/  (File System)"]
        direction LR
        CSV1["fpt_products.csv"]
        CSV2["fpt_platform_products.csv"]
        CSV3["phongvu_products.csv"]
        CSV4["phongvu_platform_products.csv"]
    end

    MAIN --> FPT
    MAIN --> PV
    FPT --> BASE
    PV  --> BASE
    FPT --> NORM
    PV  --> NORM
    FPT --> PT
    PV  --> PT
    FPT --> PW
    PV  --> PW
    PW  --> BS
    BS  --> FPT
    BS  --> PV
    FPT -->|"clean_and_save()\nper category"| CSV1
    FPT -->|"clean_and_save()\nper category"| CSV2
    PV  -->|"clean_and_save()\nper category"| CSV3
    PV  -->|"clean_and_save()\nper category"| CSV4
```

### Responsibility
Pure data extraction. Each crawler scrapes one platform and writes two CSV files to `crawler/output/`. No database writes, no Typesense calls.

### Base Class: `core/crawler.py`
```python
class Crawler(ABC):
    def __init__(self, name, output_dir, base_url): ...
    def crawl(self) -> None: ...   # abstract
```

### Concrete Crawlers

| Crawler | Platform | Platform ID | Tech |
|---|---|---|---|
| `FptTrojanPro` | FPT Shop | 7 | Playwright + BeautifulSoup + Stealth |
| `PhongVuCrawler` | Phong Vũ | 8 | Playwright + BeautifulSoup + Stealth |

### Crawl Flow (per crawler)
```
For each category URL:
  1. Launch Playwright (headless Chrome + stealth)
  2. Dismiss popups, scroll, click "Xem thêm" until page is fully loaded
  3. Parse HTML with BeautifulSoup → extract (product, platform_product) pairs
  4. Append to in-memory lists
  5. Call clean_and_save() → write/overwrite CSV (incremental, crash-safe)
```

### CSV Output Schema

**`*_products.csv`** (normalised product identity)
| Column | Type | Description |
|---|---|---|
| `normalized_name` | str | Pre-cleaned name (lowercase, no accents, no junk) |
| `slug` | str | URL-safe identifier (unique per product) |
| `brand` | str | Extracted brand name |
| `category` | str | Platform category slug |
| `main_image_url` | str | Product image URL |

**`*_platform_products.csv`** (platform-specific listing)
| Column | Type | Description |
|---|---|---|
| `product_id` | UUID | Left empty at crawl time — filled by pipeline |
| `platform_id` | int | Platform constant (7=FPT, 8=PhongVu) |
| `raw_name` | str | Original title from the platform page |
| `original_item_id` | str | Platform's own slug/ID for the listing |
| `url` | str | Full product page URL |
| `affiliate_url` | str | Affiliate link (if configured) |
| `current_price` | Decimal | Current selling price (VND) |
| `original_price` | Decimal | Original/list price (VND) |
| `in_stock` | bool | Availability |
| `last_crawled_at` | ISO 8601 | Timestamp of this crawl run |

### Text Pre-cleaning: `utils/text_parser.ProductNormalizer`
Applied by crawlers during HTML parsing and reused by the pipeline LLM stage as a pre-cleaning pass:
- Unicode NFKC normalisation → lowercase
- Remove bracketed content `[...]`, `(...)`, `【...】`
- Strip Vietnamese marketing keywords (`chính hãng`, `freeship`, `trả góp`, …)
- Remove special characters, compact model codes (`wh 1000 xm5` → `wh1000xm5`)

### Running the Crawler
```bash
# From repo root:
python -m services.crawler.main

# Or via shell wrapper (used by cron):
/bin/bash services/crawler/run_crawler.sh
```

---

## Pipeline Subsystem (ELT)

### Pipeline Component Diagram

The 4-stage ELT process, the modules that own each stage, and the data stores they interact with.

```mermaid
flowchart TD
    subgraph inputs["Inputs"]
        CSV["CSV Files\n─────────────\ncrawler/output/\n*.csv"]
    end

    subgraph pipeline["services/pipeline/"]
        MAIN2["main.py\n─────────────\nOrchestrator\nRuns stages 0–3b\nin sequence"]

        S0["db.py · ensure_staging_schema()\n─────────────\nStage 0 — Setup\nCREATE SCHEMA IF NOT EXISTS\nCREATE TABLE IF NOT EXISTS\nALTER TABLE migrations"]

        S1["staging_loader.py\n─────────────\nStage 1 — Extract → Bronze\nRead CSV with stdlib csv\nON CONFLICT upsert\nllm_status = 'pending'\nSmart re-run: only reset\nif raw_name changed"]

        S2["llm_normalizer.py\n─────────────\nStage 2 — Transform\nBatch 20 names per call\nProductNormalizer pre-clean\nStateless LLM conversation\nParse JSON → product_type\nbrand · model · specs[]\nDerive normalized_name in code\nRetry × 3 (exp. backoff)"]

        S3A["product_resolver.py\n─────────────\nStage 3a — Dedup\nSearch Typesense num_typos=0\nBrand match check\nReturn ResolvedProduct list\nproduct_id=None → new"]

        S3B["persister.py\n─────────────\nStage 3b — Load → Gold\nUpsert platforms\nInsert new products RETURNING id\nUpsert platform_products (×200)\nTypesense upsert (new only)"]

        CFG["config.py\n─────────────\nLoads .env\nAll constants"]
    end

    subgraph ext["External Services"]
        LLM["LiteRTLM Gateway\n─────────────\nPOST /api/conversations\nPOST /api/conversations/{name}/messages\nDELETE /api/conversations/{name}"]
        TS["Typesense\n─────────────\ncollection: products\nFields: id · normalized_name · slug"]
    end

    subgraph stagingdb2["Staging DB  (producthunter_staging)"]
        RAW["staging.raw_crawl\n─────────────\nBronze layer\nllm_status: pending|done|failed"]
        NP["staging.normalized_products\n─────────────\nSilver layer\nproduct_type · brand · model\nspecs (JSONB) · normalized_name"]
    end

    subgraph serverdb2["Server DB  (db_producthunt)"]
        PROD["products\nbrand · normalized_name · slug\ncategory · main_image_url"]
        PP["platform_products\nproduct_id · platform_id\nraw_name · price · in_stock"]
        PLAT["platforms\nid · name · base_url"]
    end

    MAIN2 --> S0
    S0 --> S1
    S1 --> S2
    S2 --> S3A
    S3A --> S3B
    CFG -.->|"config"| S1
    CFG -.->|"config"| S2
    CFG -.->|"config"| S3A
    CFG -.->|"config"| S3B

    CSV -->|"csv.DictReader"| S1
    S1 -->|"INSERT / ON CONFLICT"| RAW
    RAW -->|"SELECT pending"| S2
    S2 -->|"POST batch prompt"| LLM
    LLM -->|"JSON array reply"| S2
    S2 -->|"INSERT normalized results"| NP
    S2 -->|"UPDATE llm_status"| RAW
    NP -->|"JOIN raw_crawl WHERE done"| S3A
    S3A -->|"search num_typos=0"| TS
    TS  -->|"hit / miss"| S3A
    S3B -->|"UPSERT"| PLAT
    S3B -->|"INSERT RETURNING id"| PROD
    S3B -->|"UPSERT batch 200"| PP
    S3B -->|"upsert_document (new only)"| TS
```

### Responsibility
Reads crawler CSVs → normalises product names using an LLM → loads clean data into the production server DB and Typesense search index.

### Databases

| Database | Purpose | Config key |
|---|---|---|
| `producthunter_staging` | Bronze + Silver staging layers | `STAGING_DB_URL` |
| `db_producthunt` | Production server DB (Gold) | `SERVER_DB_URL` |

Both are on the same Postgres instance; the pipeline opens two separate connections.

### Staging Schema (auto-created on first run)

```sql
-- Bronze layer: raw crawled data, one row per platform listing
staging.raw_crawl (
    id               UUID PK,
    source_file      TEXT,           -- e.g. 'fpt_platform_products.csv'
    platform_id      INT,
    raw_name         TEXT,           -- original title from platform
    original_item_id TEXT,
    url, affiliate_url, current_price, original_price, in_stock,
    main_image_url, last_crawled_at,
    ingested_at      TIMESTAMPTZ,
    llm_status       TEXT            -- 'pending' | 'done' | 'failed'
    UNIQUE (platform_id, original_item_id)
)

-- Silver layer: LLM normalisation results
staging.normalized_products (
    raw_id           UUID FK → staging.raw_crawl(id),
    normalized_name  TEXT,           -- derived: "<brand> <model> <specs...>"
    brand            TEXT,
    product_type     TEXT,           -- e.g. 'smartphone', 'laptop'
    model            TEXT,           -- e.g. 'Poco M7 Pro 5G'
    specs            JSONB,          -- [{name, value}, ...]
    category         TEXT,           -- alias of product_type
    llm_model        TEXT,
    normalized_at    TIMESTAMPTZ
)
```

### Pipeline Stages

#### Stage 1 — `staging_loader.py` (Extract → Bronze)
- Reads CSVs with stdlib `csv` (no pandas dependency)
- Upserts into `staging.raw_crawl` via `ON CONFLICT (platform_id, original_item_id)`
- Smart re-run logic: only resets `llm_status = 'pending'` when `raw_name` changed (product was renamed on platform). Price-only updates keep `llm_status = 'done'`.

#### Stage 2 — `llm_normalizer.py` (Transform via LiteRTLM)
- Queries `WHERE llm_status = 'pending'` in batches of `LLM_BATCH_SIZE` (default 20)
- Pre-cleans each `raw_name` with `ProductNormalizer` before sending to reduce LLM prompt noise
- Creates a **stateless conversation** on LiteRTLM per batch → sends one blocking message → deletes conversation
- LLM prompt returns structured JSON per product: `{ product_type, brand, model, specs: [{name, value}] }`
- `normalized_name` is **derived in code** from `brand + model + spec values` (not from LLM) — deterministic dedup key
- On network error: retries up to `LLM_MAX_RETRIES` (default 3) with exponential backoff (2s, 4s, 8s)
- On JSON parse failure: marks rows `'failed'`, continues — they will be retried on the next pipeline run
- Writes results to `staging.normalized_products`, marks `llm_status = 'done'`

#### Stage 3a — `product_resolver.py` (Dedup via Typesense)
- Joins `staging.raw_crawl` + `staging.normalized_products WHERE llm_status = 'done'`
- For each row: searches Typesense with `num_typos=0` (strict — avoids false merges across brands)
- If top hit's brand matches → reuse existing `product_id` (`is_new=False`)
- Otherwise → mark as new (`product_id=None`, `is_new=True`)
- Returns `List[ResolvedProduct]` dataclass

#### Stage 3b — `persister.py` (Load → Gold)
1. **Upsert platforms** — inserts/updates `platforms` table from `PLATFORM_META` dict
2. **Insert new products** — `INSERT INTO products ... ON CONFLICT (slug) DO UPDATE ... RETURNING id, slug` to retrieve generated UUIDs
3. **Upsert platform_products** — batch of 200 rows, `ON CONFLICT (platform_id, original_item_id) DO UPDATE`
4. **Typesense sync** — only new products are indexed (avoids redundant upserts for existing products)

### LiteRTLM Integration

Uses the `/api/conversations` REST API (stateless mode):

```
POST /api/conversations        { name: "pipeline-norm-<uuid>", stateless: true }
POST /api/conversations/{name}/messages  { message: "<prompt>" }
→ { reply: "[{...}, ...]" }
DELETE /api/conversations/{name}
```

Auth: `Authorization: Bearer <LITELLM_API_KEY>` (preferred) or JWT login fallback.

### Running the Pipeline
```bash
# From repo root:
python -m services.pipeline.main

# Or via shell wrapper (used by cron):
/bin/bash services/pipeline/run_pipeline.sh
```

### Cron Schedule (recommended)
```cron
0 1 * * *  /bin/bash /path/to/services/crawler/run_crawler.sh   >> .../output/cron.log 2>&1
0 3 * * *  /bin/bash /path/to/services/pipeline/run_pipeline.sh >> .../pipeline/logs/pipeline.log 2>&1
```
2-hour gap ensures the crawler finishes before the pipeline starts.

---

## Configuration Reference (`services/.env`)

| Key | Used by | Description |
|---|---|---|
| `POSTGRES_HOST/PORT/USER/PASSWORD/DB` | Crawler (legacy), Pipeline fallback | Postgres connection parts |
| `SERVER_DB_URL` | Pipeline | Full DSN for production server DB |
| `STAGING_DB_URL` | Pipeline | Full DSN for staging DB |
| `TYPESENSE_HOST/PORT/API_KEY/PROTOCOL` | Pipeline | Typesense connection |
| `LITELLM_BASE_URL` | Pipeline | LiteRTLM gateway base URL |
| `LITELLM_API_KEY` | Pipeline | API key for LiteRTLM (preferred auth) |
| `LITELLM_USERNAME/PASSWORD` | Pipeline | JWT login fallback (if no API key) |
| `LLM_BATCH_SIZE` | Pipeline | Names per LLM call (default: 20) |
| `LLM_MAX_RETRIES` | Pipeline | LLM call retry limit (default: 3) |

---

## Idempotency Guarantees

| Operation | Behaviour on re-run |
|---|---|
| Stage 1 CSV load | `ON CONFLICT` upsert — no duplicates; only resets `llm_status` if `raw_name` changed |
| Stage 2 LLM normalize | Only processes `llm_status = 'pending'` rows — already-normalized rows are skipped |
| Stage 3 product insert | `ON CONFLICT (slug) DO UPDATE` — safe to re-run |
| Stage 3 platform_products | `ON CONFLICT (platform_id, original_item_id) DO UPDATE` — safe to re-run |
| Typesense sync | `upsert_document` — idempotent |

---

## End-to-End Data Flow

```mermaid
flowchart LR
    subgraph WEB["E-Commerce Platforms"]
        W1["fptshop.com.vn"]
        W2["phongvu.vn"]
    end

    subgraph CRAWL["Crawler  (cron 01:00)"]
        C1["FptTrojanPro"]
        C2["PhongVuCrawler"]
    end

    subgraph FILES["File System\ncrawler/output/"]
        F1["fpt_products.csv\nfpt_platform_products.csv"]
        F2["phongvu_products.csv\nphongvu_platform_products.csv"]
    end

    subgraph ELT["Pipeline  (cron 03:00)"]
        P1["Stage 1\nstaging_loader\nCSV → Bronze"]
        P2["Stage 2\nllm_normalizer\nTransform"]
        P3A["Stage 3a\nproduct_resolver\nDedup"]
        P3B["Stage 3b\npersister\nLoad"]
    end

    subgraph STAGING["Staging DB\nproducthunter_staging"]
        S1DB[("staging.raw_crawl\n(Bronze)")]
        S2DB[("staging.normalized_products\n(Silver)")]
    end

    subgraph LLM_EXT["LiteRTLM Gateway"]
        LLM2["Stateless conversation\nbatch 20 names\n→ product_type · brand\n   model · specs[]"]
    end

    subgraph SEARCH["Typesense"]
        TS2["products collection\nnormalized_name · slug"]
    end

    subgraph GOLD["Server DB  db_producthunt"]
        G1[("products")]
        G2[("platform_products")]
        G3[("platforms")]
    end

    W1 -->|"Playwright scrape"| C1
    W2 -->|"Playwright scrape"| C2
    C1 -->|"CSV write"| F1
    C2 -->|"CSV write"| F2
    F1 -->|"read"| P1
    F2 -->|"read"| P1
    P1 -->|"upsert"| S1DB
    S1DB -->|"pending rows"| P2
    P2 <-->|"REST API"| LLM2
    P2 -->|"insert"| S2DB
    S2DB -->|"done rows"| P3A
    P3A <-->|"search"| TS2
    P3A -->|"ResolvedProduct list"| P3B
    P3B -->|"upsert"| G1
    P3B -->|"upsert"| G2
    P3B -->|"upsert"| G3
    P3B -->|"upsert_document"| TS2
```
