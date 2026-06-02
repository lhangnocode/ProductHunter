# Crawler service

## Architecture

The crawler service is modular and extensible. It focuses on batch crawling, normalization, and ingestion with optional Typesense search updates. Components:

1. **Entry Point**: `services/crawler/main.py` orchestrates one or more crawler runs (cron-safe).
2. **Base Crawler Class**: `services/crawler/core/crawler.py` defines the shared interface and owns a `StorageManager` instance.
3. **Specific Crawler Implementations**: Platform crawlers for CellphoneS, FPT Shop, and Phong Vũ use Playwright + BeautifulSoup and emit normalized data.
4. **Storage Layer**: `services/crawler/core/storage/` provides DB and Typesense handlers plus ETL helpers.
5. **Error Handling and Logging**: Crawl errors are logged per category; Typesense failures are best-effort.

### Architecture Diagram

```
                   +---------------------+
                   |   Crawler Manager   |
                   |  schedule/run jobs  |
                   +----------+----------+
                              |
                              v
                   +---------------------+         +---------------------+
                   |  Base Crawler Class |<------->|     Data Storage    |
                   |  fetch/parse/emit   |         | schema/constraints  |
                   +----------+----------+         | persist/files/ETL   |
                              |                   +----------+----------+
          +------------+------------+-------------+          |
          |            |            |             |          |
          v            v            v             v          v
+----------------+ +----------------+ +----------------+
| CellphoneS     | | FPT Shop       | | Phong Vu       |
| crawler        | | crawler        | | crawler        |
+-------+--------+ +-------+--------+ +-------+--------+
        |                  |                  |
        +------------------+------------------+
                                |
                                v
                   +---------------------+
                   |  Normalized Output  |
                   |   to Data Storage   |
                   +---------------------+

   Error Handling + Logging (cross-cutting across all components)
```

## Components
- **Entry Point**: `services/crawler/main.py` is designed for cron execution and orchestrates crawler runs.
- **Base Crawler**: `services/crawler/core/crawler.py` defines the abstract interface and owns a shared `StorageManager`.
- **Storage Manager (Singleton)**: `services/crawler/core/storage/storage_manager.py` wires DB + Typesense handlers once per process.
- **Database Handler**: `services/crawler/core/storage/database_handler.py` provides a lightweight connection + query layer and loads `.env` DB settings.
- **Typesense Handler**: `services/crawler/core/storage/typesense_handler.py` ensures the `products` collection (with infix-enabled fields), bulk import, and search updates.
- **Crawler Implementations**: CellphoneS, FPT Shop, and Phong Vũ crawlers extract product fields and map to server models.

Current entry point note: `services/crawler/main.py` imports all three crawler
classes, but only `PhongVuCrawler` is enabled in the default checked-in script.
Enable the FPT Shop and CellphoneS calls in that file when a full three-site run
is intended. Platform IDs follow the crawler CSV pipeline convention:
`7 = FPT Shop`, `8 = Phong Vũ`, and `9 = CellphoneS`.

## Data Models (Crawler Output)
- **products**: `normalized_name`, `slug`, `brand`, `category`, `main_image_url`
- **platform_products**: `product_id`, `platform_id`, `raw_name`, `original_item_id`, `url`, `affiliate_url`, `current_price`, `original_price`, `in_stock`, `last_crawled_at`

## Runtime Flow (Batch)
1. **Cron triggers** `services/crawler/main.py`.
2. **Crawler loads** pages per category (Playwright), expands listings, and parses DOM.
3. **Crawler writes CSV snapshots** to `services/crawler/output`.
4. **Pipeline utilities** load CSVs into staging, normalize names, resolve products, persist gold tables, and update Typesense.
5. **Backend ingestion APIs** remain available for controlled product and platform-product upserts with `X-API-Key`.

Current implementation note: the crawler classes themselves write CSV files; they
do not directly POST to the FastAPI crawler ingestion endpoints. In
`services/pipeline/main.py`, the Stage 1 CSV load and later persistence stages
are currently commented out, so the checked-in pipeline entry point primarily
ensures schemas/Typesense and runs LLM normalization.

## Price Alert Trigger Integration
The backend trigger API is implemented, but automatic post-crawl invocation from
the crawler is not wired yet.

After a crawler run completes and updated `platform_products.current_price`
values have been persisted, the crawler/server should trigger the existing API
once. The implemented API checks the active price-alert list for the
authenticated user and computes the current lowest in-stock price on the server:

```http
POST /api/v1/price_alerts/trigger
```

```json
{}
```

Implemented API behavior:

1. `POST /api/v1/price_alerts/trigger` requires a Bearer token today.
2. Body `{}` checks all active alerts for the authenticated user.
3. Body `{"product_id": "..."}` narrows the check to one product.
4. Matching alerts are marked as triggered and email sending is queued via FastAPI background tasks.

Planned crawler integration:

1. Finish persisting updated crawl prices to `platform_products`.
2. Call a system-level alert trigger once after persistence.
3. Let the backend iterate through active price alerts and compute `MIN(current_price)` from in-stock platform products for each product.
4. Let the backend price-alert service evaluate active alerts where `target_price >= current_lowest_price`.
5. Let the backend queue price-drop emails and mark matched alerts as triggered.

Open implementation decisions:

- Authentication should use a server-to-server credential or API key rather than a normal user token.
- The trigger should run once per affected product, not once per platform product row, to avoid duplicate alert checks.
- The crawler should treat alert-trigger failures as non-fatal after DB persistence, but should log enough context to retry later.
- A future implementation should add tests that verify the post-crawl trigger call and duplicate-prevention behavior.

## Scheduling
- Shell wrapper: `services/crawler/run_crawler.sh` runs `python -m services.crawler.main` from the repo root.
- Cron template: `services/crawler/crawler.cron` schedules daily runs at 1 AM (edit paths before installing).
- Full flow wrapper: `services/run_full_pipeline.sh` runs crawl, CSV staging + LLM normalization, then `migrate_normalized_data`.
- Useful full-flow flags: `SKIP_CRAWL=1`, `SKIP_PIPELINE=1`, `SKIP_MIGRATE=1`, `STRICT_CSV=1`, `LOG_DIR=services/logs`.
- When `STRICT_CSV=1`, set `EXPECTED_CSV_FILES` if only a subset of crawlers is enabled.

## Pipeline LLM Provider
- Stage 2 normalization defaults to OpenAI through `LLM_PROVIDER=openai`.
- Required OpenAI settings in `services/.env`: `OPENAI_API_KEY`.
- Optional OpenAI-compatible gateway setting: `OPENAI_BASE_URL` (for example `http://localhost:8080/v1`; leave unset for OpenAI's hosted API).
- Optional OpenAI settings: `OPENAI_MODEL` (default `gpt-5.4-mini`), `OPENAI_TIMEOUT_SECONDS`, `OPENAI_MAX_OUTPUT_TOKENS`.
- LiteRTLM remains available only as a legacy fallback by setting `LLM_PROVIDER=litertlm` and the existing `LITELLM_*` variables.

## Error Handling
- Crawl errors are logged per category; the crawler continues with the next category.
- Typesense updates are best-effort; failures do not block DB persistence.
