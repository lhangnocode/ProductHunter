# Crawler service

## Architecture

The crawler service is designed to be modular and extensible, allowing for easy integration of new crawlers for different e-commerce platforms. The architecture consists of the following components:

1. **Base Crawler Class**: An abstract class that defines the common interface and functionality for all crawlers. This class can be extended to create specific crawlers for different platforms.
2. **Specific Crawler Implementations**: Concrete implementations of the base crawler class for specific e-commerce platforms (e.g., Amazon, eBay, etc.). Each implementation will handle the unique structure and requirements of its respective platform.
3. **Crawler Manager**: A component responsible for managing the lifecycle of crawlers, including instantiation, execution, and scheduling.
4. **Data Storage**: A peer component to the base crawler that defines schema and constraints, and exposes public functions for persistence, file handling, and optional ETL helpers used by specific crawlers when needed.
5. **Error Handling and Logging**: A system for handling errors and logging the crawling process for debugging and monitoring purposes.

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
- **Entry Point**: `services/crawler/main.py` is designed for cron execution and orchestrates one or more crawler runs.
- **Base Crawler**: `services/crawler/core/crawler.py` defines the abstract interface and owns a shared `StorageManager`.
- **Storage Manager (Singleton)**: `services/crawler/core/storage/storage_manager.py` wires DB + Typesense handlers once per process.
- **Database Handler**: `services/crawler/core/storage/database_handler.py` provides a lightweight connection + query layer and loads `.env` DB settings.
- **Typesense Handler**: `services/crawler/core/storage/typesense_handler.py` handles collection creation, bulk import, and search updates.
- **Crawler Implementations**: e.g. FPT and Phong Vu crawlers extract product fields and map to server models.

## Data Models (Crawler Output)
- **products**: `normalized_name`, `slug`, `brand`, `category`, `main_image_url`
- **platform_products**: `product_id`, `platform_id`, `raw_name`, `original_item_id`, `url`, `affiliate_url`, `current_price`, `original_price`, `in_stock`, `last_crawled_at`

## Runtime Flow (Batch)
1. **Cron triggers** `services/crawler/main.py`.
2. **Crawler loads** pages per category (Playwright), expands listings, and parses DOM.
3. **Normalize + map** raw fields into `products` and `platform_products`.
4. **For each new platform product**:
   - **Fuzzy match** in Typesense using `normalized_name` / `slug`.
   - **If match found**: use the returned product `id`.
   - **If no match**: create a new product in PostgreSQL, then upsert that product into Typesense.
   - **Insert/update platform product** in PostgreSQL with the resolved `product_id`.
5. **Persist CSV snapshots** to `services/crawler/output` for recovery/debug.

## Error Handling
- Crawl errors are logged per category; the crawler continues with the next category.
- Typesense updates are best-effort; failures do not block DB persistence.
