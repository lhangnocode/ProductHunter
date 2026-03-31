# Project Specs: ProductHunter

## Purpose
ProductHunter is a micro-SaaS focused on tech products. It aggregates prices from multiple e-commerce platforms and presents comparison views, historical price trends, wishlist tracking, and price alerts.

## Goals
- Compare prices for tech products across supported marketplaces (Shopee, Lazada, Tiki, etc.).
- Provide search and quick discovery of matching products.
- Track price history for spotting real discounts and trending deals.
- Allow users to save products (wishlist) and set price alerts.
- Ingest catalog and price data from crawlers through a controlled API.

## Non-Goals (Current Scope)
- General product categories outside of tech.
- Checkout, payments, or marketplace order flows.
- Full user authentication flows in the UI (users exist only in the DB schema).

## Users & Roles
- End users: search/compare products, save wishlist items, set alerts.
- Crawler operators: ingest product and platform-product data via DEV API key.

## Core Features (Implemented)
- Product search by name (Typesense with Postgres fallback on `normalized_name`/`slug`).
- Product list retrieval (pagination via `skip`/`limit`).
- Platform management (create/list).
- Crawler ingestion endpoints for products and platform products (DEV API key required).
- Frontend UI: tabs for Search/Compare, Trending Deals, Wishlist, Price Alerts; product detail view with price history chart.

## Planned / Partially Implemented
- Browser extension for in-page comparison (mentioned in UI and docs; not implemented in repo).

## System Architecture
- Monorepo layout:
  - `client`: Vite + React frontend.
  - `server`: FastAPI backend, async SQLAlchemy, PostgreSQL.
  - `services`: crawler scripts for marketplaces.
  - `docs`: documentation and specs.
- Communication:
  - Frontend calls API at `http://localhost:8000/api/v1` for search.
  - API search uses Typesense for ranking and falls back to Postgres when Typesense is unavailable.
  - Crawlers POST data to API endpoints with `X-API-Key`.

## Data Model (PostgreSQL)
- `users`: basic profile + plan (free/premium enum).
- `products`: normalized product identity (slug, brand, category, image).
- `platforms`: marketplace metadata and affiliate config.
- `platform_products`: listing data per platform (prices, URLs, stock, crawl timestamp).
- `price_records`: time-series prices for historical charts.
- `wish_list`: user-product tracking.
- `price_alerts`: target price thresholds and status.

## API Surface (v1)
- `GET /` and `GET /health` for service checks.
- `GET /api/v1/products/search?name=...&limit=&page=` returns products via Typesense (fallback to Postgres).
- `GET /api/v1/products?skip=&limit=` list products.
- `POST /api/v1/platforms` create a platform.
- `GET /api/v1/platforms` list platforms.
- `POST /api/v1/crawler/products` upsert product (DEV API key).
- `POST /api/v1/crawler/platform-products` upsert platform product (DEV API key).

## Crawling & Ingestion
- Python crawlers in `services/crawler/` (Playwright + BeautifulSoup) for supported platforms.
- Entry point: `services/crawler/main.py` (cron-safe), invoked via `services/crawler/run_crawler.sh`.
- Crawlers output CSV snapshots to `services/crawler/output/` and POST to the API for ingestion.
- Upload endpoints require `X-API-Key` matching `DEV_API_KEY` in server `.env`.
- Typesense `products` collection is created/ensured by crawler runs (infix enabled for `normalized_name`, `slug`).

## Frontend UX
- Tabs: Search/Compare, Trending Deals, Wishlist, Price Alerts.
- Product detail includes platform comparison and a price history chart (Recharts).
- Uses Tailwind CSS, Lucide icons, and Motion for transitions.

## Configuration & Secrets
- Server config via `.env` (see `server/.env.example`).
- Key settings: Postgres connection, `DEV_API_KEY`, `TYPESENSE_API_KEY`, `TYPESENSE_HOST`, `TYPESENSE_PORT`, `TYPESENSE_PROTOCOL`, CORS origins.

## Local Development
- Backend:
  - `pip install -r server/requirements.txt`
  - `cp server/.env.example server/.env`
  - `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` (from `server/`).
- Frontend:
  - `npm install` then `npm run dev` in `client/`.
- Docker (API + Postgres + Typesense): `docker compose up -d` in `server/`.

## Deployment
- GitHub Actions deploys to a host over Tailscale + SSH.
- Remote runs `docker compose up -d --build` in `server/`.

## Testing
- No test suites are present in the repository.
