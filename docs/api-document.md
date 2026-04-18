# ProductHunter API Documentation

FastAPI server exposing product, platform, price-tracking, wishlist, and authentication endpoints.

- **Base URL:** `http://{HOST}:{PORT}` (default `http://0.0.0.0:3000`)
- **API prefix:** `/api/v1`
- **OpenAPI spec:** `/api/v1/openapi.json`
- **Interactive docs:** `/docs` (Swagger), `/redoc`

## Root / Health

| Method | Path       | Auth | Description                         |
|--------|------------|------|-------------------------------------|
| GET    | `/`        | —    | Welcome message + API version       |
| GET    | `/health`  | —    | Liveness probe. Returns `{status: "ok"}` |

---

## Authentication

### Token model

All protected endpoints expect `Authorization: Bearer <access_token>`.
Tokens are JWT, signed with `SECRET_KEY` (HS256).

- **Access token** — default 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh token** — default 7 days (`REFRESH_TOKEN_EXPIRE_DAYS`)

### `POST /api/v1/auth/register`
Create a new user account.

**Body** (`UserCreate`): `{ email, password, full_name }`
**Response** (`UserResponse`): user object.
Fails `400` if email already exists.

### `POST /api/v1/auth/login`
OAuth2 password flow. Form-encoded (`application/x-www-form-urlencoded`).

**Body:** `username` (email), `password`
**Response:** `{ access_token, refresh_token, token_type: "bearer" }`

### `GET /api/v1/auth/me`  *(auth required)*
Returns the authenticated user's profile.

### `POST /api/v1/auth/premium-feature`  *(auth required, premium plan)*
Premium-plan-only demo endpoint. Returns a personalized message.

### `POST /api/v1/auth/refresh`
Exchange a refresh token for a new access token.

**Body:** `{ "refresh_token": "..." }`
**Response:** `{ access_token, refresh_token, token_type }`

### `GET /api/v1/auth/{provider}/login`
Redirects to the OAuth provider's consent page. Supported providers: `google`, `github`.

**Query:** optional `frontend_url` — where to redirect after successful login (must be whitelisted).

### `GET /api/v1/auth/{provider}/callback`
OAuth callback. Creates a new user on first login, then redirects to the frontend:

```
{FRONTEND_URL}/?access_token=...&refresh_token=...
```

---

## Products

### `GET /api/v1/products/`
Paginated list of all products.

**Query:** `skip` (int, default 0), `limit` (int, default 100)
**Response:** array of product objects.

### `GET /api/v1/products/search`
Full-text search across normalized product names.

**Query:**
- `q` — keyword, min length 2 (required)
- `page` — default 1
- `limit` — default 20, max 100

**Response** (`SearchPaginatedResponse`):
```json
{
  "keyword": "string",
  "current_page": 1,
  "total_pages": 10,
  "total_results": 200,
  "data": [ProductResponse, ...]
}
```

### `GET /api/v1/products/searchAll`
Same as `/search`, but `data` is a flat list of platform-product listings across all matching products.

### `GET /api/v1/products/compare`
Search + cross-platform price comparison using live DB data.

**Query:** `q` (min 2 chars, required)
**Response** (`SearchCompareResponse`):
```json
{
  "keyword": "string",
  "total_results": 5,
  "data": [
    {
      "id": "uuid",
      "normalized_name": "...",
      "product_name": "...",
      "slug": "...",
      "main_image_url": "...",
      "lowest_price": 5200000,
      "platforms": [
        {
          "platform_id": 1,
          "url": "...",
          "affiliate_url": "...",
          "current_price": 5200000,
          "original_price": 5990000,
          "in_stock": true,
          "last_crawled_at": "2026-03-29T10:00:00Z"
        }
      ]
    }
  ]
}
```
Results are sorted by `lowest_price` ascending.

### `GET /api/v1/products/compare2`
Identical shape to `/compare` but uses a hardcoded mock data set for demos. Still hits the DB to find matching products by `normalized_name ILIKE`.

---

## Platforms

### `POST /api/v1/platforms/`
Create a new e-commerce platform record.

**Body** (`PlatformCreateRequest`): `{ name, base_url, affiliate_config }`
**Response** (`PlatformResponse`): platform with auto-generated `id`.

### `GET /api/v1/platforms/`
List all platforms.

---

## Platform Products

Platform-products are individual product listings on a specific platform (e.g. "iPhone 15 on Shopee").

### `GET /api/v1/platform_products/platform-products`
List all platform-products with pagination.

**Query:** `limit` (1-100, default 10), `offset` (default 0)

### `GET /api/v1/platform_products/platform-products/search`
Search platform-products by product name or slug.

**Query:** `name` (required), `limit` (1-100, default 20), `page` (default 1)

### `GET /api/v1/platform_products/platform-products/by-product-id`
All listings for a specific canonical product.

**Query:** `product_id` (UUID, required), `limit`, `page`

### `GET /api/v1/platform_products/platform-products/trending`
Trending deals — items that are at their lowest recorded price, sorted by discount magnitude.

**Query:** `limit` (1-100, default 20)
**Response** (`TrendingDealResponse[]`): deal entries with discount info.

---

## Price Records

Historical price snapshots per platform-product, used for trend charts.

### `GET /api/v1/price_record/price-records`
Paginated list, newest first.

**Query:** `limit` (1-100, default 20), `offset` (default 0)

### `GET /api/v1/price_record/price-records/{platform_product_id}`
Full history for one listing, oldest → newest.

### `POST /api/v1/price_record/price-records`
Insert a single price record.

**Body** (`PriceRecordCreateRequest`):
```json
{
  "platform_product_id": "uuid",
  "price": 5200000,
  "original_price": 5990000,
  "is_flash_sale": false,
  "recorded_at": "2026-04-15T10:00:00Z"   // optional
}
```
Returns `404` if `platform_product_id` does not exist.

### `POST /api/v1/price_record/price-records/batch`
Insert multiple records at once. Invalid rows (unknown platform_product_id) are silently skipped.

**Body:** `PriceRecordCreateRequest[]`
**Response:** array of created records.

### `GET /api/v1/price_record/price-analysis/{platform_product_id}`
Compute a status analysis (is this current price historically low?).

**Query:** `current_price` (float), `original_price` (float)

---

## Price Alerts  *(auth required)*

User-defined price thresholds that send email notifications when triggered.

### `POST /api/v1/price_alerts/`
Create or update an alert for a product.

**Body** (`PriceAlertCreate`): target product + desired price.
**Response** (`PriceAlertResponse`).

### `GET /api/v1/price_alerts/`
List alerts for the current user.

### `DELETE /api/v1/price_alerts/{product_id}`
Remove a user's alert for a product.

### `POST /api/v1/price_alerts/trigger`
Triggered by the crawler/pipeline when a new lowest price is observed. Queues notification emails to all users who have a qualifying alert.

**Body:**
```json
{ "product_id": "uuid", "current_lowest_price": 4800000 }
```
Runs in the background; responds immediately.

---

## Wishlist  *(auth required)*

### `POST /api/v1/wish_lists/`
Add a product to the authenticated user's wishlist.

**Body** (`WishListCreate`): `{ product_id: UUID }`

### `GET /api/v1/wish_lists/`
Get the current user's wishlist.

### `DELETE /api/v1/wish_lists/{product_id}`
Remove a product from wishlist.

---

## Crawler Ingestion  *(dev API key required)*

**All routes in this section require the header `X-API-Key: {DEV_API_KEY}`.**
These are the endpoints the crawler/pipeline uses to push normalized data into the server.

### `POST /api/v1/crawler/products`
Upsert a canonical product (brand/model/category + image).

**Body** (`ProductIngestRequest`)
**Response** (`ProductIngestResponse`)

### `POST /api/v1/crawler/platform-products`
Bulk-upsert platform-product listings. Every upsert also creates a `PriceRecord` so historical pricing is retained on every crawl.

**Body:** `PlatformProductIngestRequest[]`
**Response:** `PlatformProductIngestResponse[]`
Upsert key: `(platform_id, original_item_id)`.
If `last_crawled_at` is missing, the server stamps `now()`.

---

## Auth requirements summary

| Label | Meaning |
|--------|---------|
| `auth required` | Requires `Authorization: Bearer <access_token>` |
| `premium plan` | Requires the user's plan to be Premium |
| `dev API key required` | Requires the `X-API-Key: {DEV_API_KEY}` header |

## Environment configuration

Key variables from `server/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `3000` | Bind address |
| `POSTGRES_*` | — | Main DB connection |
| `TYPESENSE_*` | — | Search index |
| `SECRET_KEY` | — (required) | JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `DEV_API_KEY` | — | Header value for crawler ingestion |
| `GOOGLE_CLIENT_ID/SECRET` | — | Google OAuth |
| `GITHUB_CLIENT_ID/SECRET` | — | GitHub OAuth |
| `FRONTEND_URL` / `BACKEND_URL` | — | OAuth redirect base URLs |
| `MAIL_*` | — | SMTP for price-alert emails |
| `ALLOWED_ORIGINS` | `["*"]` | CORS |
