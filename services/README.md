# Crawler service

## Architecture

The crawler service is modular and extensible. It focuses on batch crawling, normalization, and ingestion with optional Typesense search updates. Components:

1. **Entry Point**: `services/crawler/main.py` orchestrates one or more crawler runs (cron-safe).
2. **Base Crawler Class**: `services/crawler/core/crawler.py` defines the shared interface and owns a `StorageManager` instance.
3. **Specific Crawler Implementations**: Platform crawlers (FPT, Phong Vũ) use Playwright + BeautifulSoup and emit normalized data.
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
          +-------------------+-------------------+          |
          |                                       |          |
          v                                       v          v
+-----------------------+              +-----------------------+
| Specific Crawler A    |              | Specific Crawler B    |
| site adapters/parsers |              | site adapters/parsers |
+-----------+-----------+              +-----------+-----------+
            |                                       |
            +-------------------+-------------------+
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
- **Crawler Implementations**: FPT and Phong Vũ crawlers extract product fields and map to server models.

## Data Models (Crawler Output)
- **products**: `normalized_name`, `slug`, `brand`, `category`, `main_image_url`
- **platform_products**: `product_id`, `platform_id`, `raw_name`, `original_item_id`, `url`, `affiliate_url`, `current_price`, `original_price`, `in_stock`, `last_crawled_at`

## Runtime Flow (Batch)
1. **Cron triggers** `services/crawler/main.py`.
2. **Crawler loads** pages per category (Playwright), expands listings, and parses DOM.
3. **Normalize + map** raw fields into `products` and `platform_products`.
4. **Ensure Typesense collection** (`products`) exists with infix-enabled fields.
5. **For each new platform product**:
   - **Fuzzy match** in Typesense using `normalized_name` / `slug`.
   - **If match found**: use the returned product `id`.
   - **If no match**: create a new product in PostgreSQL, then upsert that product into Typesense.
   - **Insert/update platform product** in PostgreSQL with the resolved `product_id`.
6. **Persist CSV snapshots** to `services/crawler/output` for recovery/debug.

## Planned Price Alert Trigger Integration
This section documents the intended post-crawl alert flow. It is not implemented yet.

After a crawler run completes and updated `platform_products.current_price` values have been persisted, the crawler/server should trigger the existing API once. The API checks the active price-alert list and computes the current lowest in-stock price on the server:

```http
POST /api/v1/price_alerts/trigger
```

```json
{}
```

Planned flow:

1. Finish persisting updated crawl prices to `platform_products`.
2. Call `POST /api/v1/price_alerts/trigger` once.
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

## Error Handling
- Crawl errors are logged per category; the crawler continues with the next category.
- Typesense updates are best-effort; failures do not block DB persistence.
