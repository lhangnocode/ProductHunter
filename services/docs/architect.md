# Architecture — Crawler & ELT Pipeline (Rewrite)

> **Scope**: `services/crawler/` and `services/pipeline/`
> **Status**: Draft — architecture and component design

---

## 1. Design Principles

1. **Single responsibility** — every module does one thing. Parsing HTML is separate from saving data; LLM calls are separate from DB writes.
2. **Explicit over implicit** — no global singletons, no hidden `.env` loading inside library modules. Config flows in; side-effects flow out.
3. **Fail loudly, recover gracefully** — hard errors crash fast; transient errors (network, Playwright timeouts) retry with backoff and log context.
4. **Idempotent by default** — every write operation uses `ON CONFLICT ... DO UPDATE` or equivalent. Re-running any stage is always safe.
5. **Extensible platform registry** — adding a new crawler requires adding one config block, not editing three separate files.
6. **No shared state between subsystems** — crawler knows nothing about the DB or Typesense; pipeline knows nothing about Playwright.

---

## 2. High-Level Topology

```
┌────────────────────────────────────────────────────────────────┐
│  CRAWLER PROCESS  (cron 01:00)                                 │
│                                                                │
│  Platform Registry                                             │
│       │                                                        │
│       ├─ FptCrawler                                            │
│       └─ PhongVuCrawler                                        │
│             │                                                  │
│        CrawlerRunner (orchestrates, dedupes, writes CSV)       │
│             │                                                  │
│        services/crawler/output/                                │
│             *.products.csv  /  *.platform_products.csv         │
└─────────────────────────┬──────────────────────────────────────┘
                          │  File system handoff
┌─────────────────────────▼──────────────────────────────────────┐
│  PIPELINE PROCESS  (cron 03:00)                                │
│                                                                │
│  Stage 1  StagingLoader      CSV → staging.raw_crawl           │
│  Stage 2  LLMNormalizer      pending rows → LiteRTLM           │
│                              → staging.normalized_products     │
│  Stage 3a ProductResolver    Typesense dedup → product_id      │
│  Stage 3b Persister          → db_producthunt (gold)           │
│                              → Typesense index                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Crawler Subsystem

### 3.1 Components

```
services/crawler/
├── main.py                     Entry point — parses CLI args, runs CrawlerRunner
├── runner.py                   CrawlerRunner — iterates platforms, handles top-level errors
├── registry.py                 Platform registry — maps platform ID → crawler class + config
├── config.py                   Loads .env, exposes all crawler constants
│
├── base/
│   ├── crawler.py              Abstract BaseCrawler(platform_id, output_dir)
│   │                           • crawl() → List[RawProduct]   ← abstract
│   │                           • save(products)               ← concrete (CSV writer)
│   ├── browser.py              BrowserSession — Playwright lifecycle wrapper
│   │                           • launch / close / new_page
│   │                           • scroll_to_bottom()
│   │                           • click_load_more(selector)
│   │                           • wait_for_count_increase(selector, before, timeout)
│   └── parser.py               Abstract BaseParser
│                               • parse(soup, category) → List[RawProduct]   ← abstract
│
├── models/
│   └── raw_product.py          RawProduct dataclass (pure data, no methods)
│                               Fields: platform_id, raw_name, original_item_id,
│                                       url, current_price, original_price,
│                                       in_stock, category, main_image_url,
│                                       crawled_at
│
├── utils/
│   ├── text.py                 Shared text utils (slugify, normalize_ascii, parse_price)
│   │                           No class — just pure functions
│   └── normalizer.py           ProductNormalizer — junk-word pre-cleaner
│                               Reads junk list from config (not hardcoded)
│
└── impl/
    ├── fpt/
    │   ├── crawler.py          FptCrawler(BaseCrawler)
    │   │                       • Categories list (from config)
    │   │                       • crawl() → uses BrowserSession + FptParser
    │   └── parser.py           FptParser(BaseParser)
    │                           • parse(soup, category) — cardDefault block parsing
    └── phongvu/
        ├── crawler.py          PhongVuCrawler(BaseCrawler)
        │                       • crawl() → uses BrowserSession + PhongVuParser
        └── parser.py           PhongVuParser(BaseParser)
                                • parse(soup, category) — ₫-anchor algorithm
```

### 3.2 Data model: `RawProduct`

```python
@dataclass
class RawProduct:
    platform_id:      int
    raw_name:         str
    original_item_id: str
    url:              str
    current_price:    Decimal | None
    original_price:   Decimal | None
    in_stock:         bool
    category:         str
    main_image_url:   str | None
    crawled_at:       datetime        # UTC, set at parse time
```

### 3.3 CSV output (one pair of files per crawler run)

| File | Key columns |
|---|---|
| `{platform}_platform_products.csv` | All `RawProduct` fields |
| `{platform}_products.csv` | `original_item_id`, `raw_name`, `main_image_url` (lightweight identity snapshot) |

CSV is written atomically per category — append-then-dedup-on-finish. If the process crashes mid-run, partial data is preserved.

### 3.4 `BrowserSession` responsibilities
- Launch headless Chromium with Playwright-Stealth
- Dismiss cookie/popup overlays (configurable selector list)
- `scroll_and_load_all(page, load_more_text, item_selector)` — generic scroll + "Xem thêm" loop used by both crawlers
- Returns `BeautifulSoup` object when page is fully expanded
- **No parsing logic** — pure browser automation

### 3.5 `registry.py` — Platform Registry

```python
PLATFORMS = {
    7: PlatformConfig(
        id=7,
        name="FPT Shop",
        base_url="https://fptshop.com.vn",
        crawler_class=FptCrawler,
        categories=[...],          # from config
    ),
    8: PlatformConfig(
        id=8,
        name="Phong Vũ",
        base_url="https://phongvu.vn",
        crawler_class=PhongVuCrawler,
        categories=[...],
    ),
}
```

Adding a new platform = add one entry here + one `impl/` folder.

---

## 4. Pipeline Subsystem

### 4.1 Components

```
services/pipeline/
├── main.py                     Entry point — runs all stages in order, logs timing
├── config.py                   Loads .env, exposes all pipeline constants
│                               Single source of truth (no .env parsing elsewhere)
│
├── db.py                       Connection factory + schema bootstrap
│                               • get_staging_conn() / get_server_conn()
│                               • ensure_staging_schema(conn)
│                               Schema versioning via staging.schema_version table
│
├── stages/
│   ├── base.py                 Abstract PipelineStage
│   │                           • run(ctx: PipelineContext) → StageResult
│   │                           • name: str
│   ├── stage1_loader.py        StagingLoader
│   │                           • CSV → staging.raw_crawl (bronze)
│   │                           • Smart upsert: only re-normalizes if raw_name changed
│   ├── stage2_normalizer.py    LLMNormalizer
│   │                           • Batches pending rows → LiteRTLM API
│   │                           • Derives normalized_name from structured output
│   │                           • → staging.normalized_products (silver)
│   ├── stage3a_resolver.py     ProductResolver
│   │                           • Typesense dedup by normalized_name
│   │                           • Returns ResolvedProduct list
│   └── stage3b_persister.py    Persister
│                               • Upsert platforms, products, platform_products
│                               • Insert price_records
│                               • Sync Typesense index
│
├── models/
│   └── resolved_product.py     ResolvedProduct dataclass
│
├── llm/
│   ├── client.py               LiteRTLMClient
│   │                           • Stateless conversation lifecycle
│   │                           • Auth: API key preferred, JWT fallback
│   │                           • Cached auth token (not per-call)
│   │                           • Exponential backoff + circuit breaker
│   └── prompt.py               Prompt builder
│                               • PROMPT_TEMPLATE (the structured normalizer prompt)
│                               • build_prompt(names: list[str]) → str
│
└── search/
    └── typesense_client.py     Thin wrapper re-exported from crawler/core/storage
                                (same TypesenseHandler, no duplication)
```

### 4.2 `PipelineContext` — shared state across stages

```python
@dataclass
class PipelineContext:
    staging_conn:   Connection
    server_conn:    Connection
    typesense:      TypesenseHandler
    run_id:         str           # UUID, logged on every stage for tracing
    dry_run:        bool = False  # If True, no writes, log only
```

All stages receive the same `ctx`. No global state.

### 4.3 Staging DB schema (`producthunter_staging`)

```
staging.schema_version         ← migration tracking
staging.raw_crawl              ← bronze: one row per platform listing
staging.normalized_products    ← silver: LLM output, derived normalized_name
```

#### `staging.raw_crawl`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `source_file` | TEXT | e.g. `fpt_platform_products.csv` |
| `platform_id` | INT | FK to platforms |
| `raw_name` | TEXT | Original title |
| `original_item_id` | TEXT | Platform's own ID/slug |
| `url` | TEXT | |
| `affiliate_url` | TEXT | |
| `current_price` | NUMERIC | |
| `original_price` | NUMERIC | |
| `in_stock` | BOOLEAN | |
| `main_image_url` | TEXT | |
| `last_crawled_at` | TIMESTAMPTZ | |
| `ingested_at` | TIMESTAMPTZ | `DEFAULT now()` |
| `llm_status` | TEXT | `pending` \| `done` \| `failed` |
| **UNIQUE** | | `(platform_id, original_item_id)` |

#### `staging.normalized_products`

| Column | Type | Notes |
|---|---|---|
| `raw_id` | UUID PK | FK → `raw_crawl.id` |
| `normalized_name` | TEXT | Derived in code: `brand + model + specs` |
| `brand` | TEXT | From LLM |
| `product_type` | TEXT | From LLM: `smartphone`, `laptop`, … |
| `model` | TEXT | From LLM: `Poco M7 Pro 5G` |
| `specs` | JSONB | From LLM: `[{name, value}]` |
| `category` | TEXT | Alias of `product_type` |
| `llm_model` | TEXT | Which model version was used |
| `normalized_at` | TIMESTAMPTZ | |

### 4.4 LLM output schema (per product)

```json
{
  "product_type": "smartphone",
  "brand": "Xiaomi",
  "model": "Poco M7 Pro 5G",
  "specs": [
    { "name": "ram",          "value": "8GB" },
    { "name": "rom",          "value": "256GB" },
    { "name": "connectivity", "value": "5G" }
  ]
}
```

`normalized_name` is **derived in code** (not from LLM):
```
"xiaomi poco m7 pro 5g 8gb 256gb"
  └─ brand + model (compact) + RAM + ROM/storage + other specs, lowercase ASCII
```

### 4.5 `LiteRTLMClient` responsibilities
- Manages one stateless conversation per batch
- Caches JWT token for session lifetime (not re-auth per batch)
- Strips markdown code fences from response
- Validates JSON array length matches input batch count
- Distinguishes retryable errors (5xx, timeout) from permanent failures (4xx, parse)

---

## 5. Shared Utilities (no duplication)

| Utility | Location | Used by |
|---|---|---|
| `slugify(text)` | `crawler/utils/text.py` | Crawler, Pipeline |
| `normalize_ascii(text)` | `crawler/utils/text.py` | Crawler, Pipeline |
| `parse_price(text)` | `crawler/utils/text.py` | Crawler |
| `ProductNormalizer` | `crawler/utils/normalizer.py` | Crawler, Pipeline (pre-clean before LLM) |
| `TypesenseHandler` | `crawler/base/` or shared lib | Pipeline only (Resolver + Persister) |

Pipeline imports from `services.crawler.utils` — no duplication.

---

## 6. Configuration (`services/.env`)

Single `.env` file, single loader function in `services/shared/env.py` — imported by both `crawler/config.py` and `pipeline/config.py`. No other file parses `.env`.

| Key | Used by |
|---|---|
| `POSTGRES_HOST/PORT/USER/PASSWORD` | Both (base credentials) |
| `POSTGRES_DB` | Crawler (legacy fallback) |
| `SERVER_DB_URL` | Pipeline — production DB |
| `STAGING_DB_URL` | Pipeline — staging DB |
| `TYPESENSE_HOST/PORT/API_KEY` | Pipeline |
| `LITELLM_BASE_URL` | Pipeline |
| `LITELLM_API_KEY` | Pipeline |
| `FPT_CATEGORIES` | Crawler (comma-separated, overrides default list) |
| `PHONGVU_CATEGORIES` | Crawler |
| `LLM_BATCH_SIZE` | Pipeline (default: 20) |
| `LLM_MAX_RETRIES` | Pipeline (default: 3) |

---

## 7. Cron Schedule

```
# Step 1 — scrape platforms, write CSVs
0 1 * * *   python -m services.crawler.main

# Step 2 — ELT: normalize, dedup, load
0 3 * * *   python -m services.pipeline.main
```

2-hour gap ensures crawling is complete before the pipeline starts.

---

## 8. What changes from the current implementation

| Area | Current | Rewrite |
|---|---|---|
| Browser logic | Duplicated in each crawler | Shared `BrowserSession` |
| HTML parsing | Duplicated in each crawler | `BaseParser` interface, one impl per platform |
| Utility functions | Copy-pasted across 3+ files | Single `crawler/utils/text.py` |
| `.env` loading | 2 separate implementations | 1 shared loader in `shared/env.py` |
| `StorageManager` | Global singleton | Removed — DI via `PipelineContext` |
| Platform metadata | Hardcoded in `persister.py` | `registry.py` — one place |
| Category lists | Hardcoded in crawler class | Config-driven via `.env` or `registry.py` |
| Price records | `'now()'` string bug | `datetime.utcnow()` parameter |
| Schema migrations | Manual `ALTER TABLE` list | `schema_version` table |
| Logging | `print()` everywhere | Structured `logging` with stage context |
| Pipeline stages | Flat functions | `PipelineStage` interface — uniform run/log/time |
