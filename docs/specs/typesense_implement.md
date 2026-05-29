# Typesense Implementation: Product Search

## Objective
Create a minimal Typesense collection for fuzzy product-name search. PostgreSQL remains responsible for platform-product queries and aggregation.

## Source Schema (PostgreSQL)
Table: `products`
```
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    normalized_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) UNIQUE NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(255),
    main_image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Related table (optional enrichment): `platform_products`
- `product_id` UUID (FK to products)
- `current_price`, `original_price`, `in_stock`, `last_crawled_at`

## Indexing Strategy
Index one document per product, containing only the fields required for fuzzy name matching and returning the product ID. All other data stays in Postgres.

### Collection Name
- `products`

### Document Identity
The intended identity is `id` (string UUID). Current backend code has drift:

- `handler_product.TYPESENSE_COLLECTION_SCHEMA` defines only `normalized_name` and `product_name`.
- `upsert_product()` upserts documents containing only `normalized_name` and `product_name`.
- `search_product()` resolves Typesense hits back to PostgreSQL by `normalized_name`.
- `search_platform_products()` expects an `id` field in Typesense hits.

Because of that mismatch, ID-based platform-product search through Typesense may not
work until the backend schema and upsert payload include `id`.

## Typesense Collection Schema
Minimal schema (JSON):

```json
{
  "name": "products",
  "fields": [
    { "name": "normalized_name", "type": "string", "infix": true },
    { "name": "product_name", "type": "string", "infix": true }
  ]
}
```

### Field Notes
- `normalized_name`: use the same normalization pipeline as in Postgres. This is the primary search text and is currently used by `search_product()` to resolve hits back to PostgreSQL.
- `product_name`: searchable for direct product name queries.
- `id`: should be added to the current backend schema/upsert payload if platform-product search is expected to resolve Typesense hits by UUID.

## Search Configuration (Fuzzy Search)
Use these query parameters when searching:

```text
query_by=normalized_name,product_name
query_by_weights=2,4 for `/products/search`; 2,8 for `/platform_products/platform-products/search`
num_typos=2
min_len_1typo=4
min_len_2typo=7
typo_tokens_threshold=1
infix=always
drop_tokens_threshold=1
prefix=true
enable_typos_for_numeric_tokens=true
prioritize_exact_match=false
split_join_tokens=always
```

Rationale:
- High weight on `normalized_name` for primary match relevance.
- Enable `infix=always` for substring matches (useful for partial model names).
- `num_typos=2` with length thresholds improves recall for short queries while limiting noise.

## Synonyms (Optional)
Create a synonym set for common variants (e.g., “iphone 15 pro max” vs “iphone15 promax”). Example:

```json
{
  "id": "apple-iphone-variants",
  "synonyms": ["iphone 15 pro max", "iphone15 promax", "iphone 15 promax"]
}
```

## Ingestion & Sync

### Source of Truth
- PostgreSQL remains the source of truth for products.
- Typesense is used for search/read performance only.

### Initial Backfill
1. Export all products from Postgres.
2. Normalize fields.
3. Bulk import into Typesense (`/collections/products/documents/import`).

### Incremental Updates
- On product insert/update in Postgres, upsert the document in Typesense.
- Price changes in `platform_products` do not affect Typesense.

### Suggested Payload Shape

```json
{
  "normalized_name": "iphone 15 pro max 256gb",
  "product_name": "iPhone 15 Pro Max 256GB"
}
```

Target payload after fixing the ID mismatch:

```json
{
  "id": "uuid",
  "normalized_name": "iphone 15 pro max 256gb",
  "product_name": "iPhone 15 Pro Max 256GB"
}
```

## Query Examples

Search by name:

```bash
curl "http://localhost:8108/collections/products/documents/search?q=iphone&query_by=normalized_name,product_name&query_by_weights=2,8&num_typos=2&min_len_1typo=4&min_len_2typo=7&typo_tokens_threshold=1&infix=always&drop_tokens_threshold=1&prefix=true&enable_typos_for_numeric_tokens=true&prioritize_exact_match=false&split_join_tokens=always"
```

## DB Lookup Flow
1. Current `/products/search` flow: Typesense returns top hits, backend reads `document.normalized_name`, then queries Postgres by `Product.normalized_name`.
2. Intended flow: Typesense returns top `id` hits, backend queries Postgres by product UUID and joins `platform_products` to produce the comparison response.

## Indexing Constraints & Tradeoffs
- `infix=always` improves substring matching but can increase index size and latency; keep the collection focused on products only.

## Rollout Checklist
1. Create collection with schema above.
2. Implement backfill job from Postgres to Typesense.
3. Implement upsert on product create/update.
4. Wire backend search to use Typesense and resolve IDs via Postgres.
