# Project Specs: ProductHunter

## Purpose
ProductHunter is a micro-SaaS focused on tech products. It aggregates prices from multiple e-commerce platforms and presents comparison views, historical price trends, wishlist tracking, and price alerts.

## Goals
- Compare prices for tech products across supported marketplaces. Current crawler implementations target CellphoneS, FPT Shop, and Phong Vũ.
- Provide search and quick discovery of matching products.
- Track price history for spotting real discounts and trending deals.
- Allow users to save products (wishlist) and set price alerts.
- Ingest catalog and price data from crawlers through a controlled API.

## Non-Goals (Current Scope)
- General product categories outside of tech.
- Checkout, payments, or marketplace order flows.

## Users & Roles
- End users: search/compare products, save wishlist items, set alerts.
- Crawler operators: ingest product and platform-product data via DEV API key.
- Authenticated users: manage wishlist items and price alerts.

## Core Features (Implemented)
- Product search by name (Typesense with Postgres fallback on `normalized_name`/`product_name`).
- Product list retrieval (pagination via `skip`/`limit`).
- Platform management (create/list).
- Crawler ingestion endpoints for products and platform products (DEV API key required).
- Authentication: email/password registration, login, token refresh, password reset, and Google/GitHub OAuth redirects.
- Wishlist and price-alert APIs with Bearer auth.
- Trending deals and price analysis from historical `price_records`.
- ProductHunter Advisor chat endpoint for shopping recommendations.
- Frontend UI: landing screen, Search/Compare, Trending Deals, Wishlist, Price Alerts, Advisor widget, auth modal, reset-password page, and product detail view with platform comparison and price history chart.

## Planned / Partially Implemented
- Automatic crawler-to-alert trigger is not wired yet. The user-scoped `/api/v1/price_alerts/trigger` endpoint exists and can be called manually with Bearer auth.
- Browser extension exists as a Plasmo project with popup/content scripts, but its production integration path is not fully documented.

## System Architecture
- Monorepo layout:
  - `client`: Vite + React frontend.
  - `server`: FastAPI backend, async SQLAlchemy, PostgreSQL.
  - `services`: crawler scripts for marketplaces.
  - `docs`: documentation and specs.
- Communication:
  - Frontend calls `CONFIG.API_URL` from `client/src/config.ts`; the checked-in value points to the Tailscale backend, not localhost.
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
- `GET /api/v1/products/search?q=...&limit=&page=` returns products via Typesense (fallback to Postgres).
- `GET /api/v1/products?skip=&limit=` list products.
- `GET /api/v1/products/searchAll?q=...&limit=&page=` returns platform products for matching products.
- `GET /api/v1/products/compare?q=...` returns product comparison groups.
- `GET /api/v1/platform_products/platform-products/search?name=...&limit=&page=` searches platform products.
- `GET /api/v1/platform_products/platform-products/by-product-id?product_id=...&limit=&page=` lists offers for one product.
- `GET /api/v1/platform_products/platform-products/trending?limit=...` returns trending deals.
- `POST /api/v1/platforms` create a platform.
- `GET /api/v1/platforms` list platforms.
- `POST /api/v1/crawler/products` upsert product (DEV API key).
- `POST /api/v1/crawler/platform-products` upsert platform product (DEV API key).
- `GET/POST /api/v1/price_record/price-records` and `POST /api/v1/price_record/price-records/batch` manage price history.
- `GET /api/v1/price_record/price-analysis/{platform_product_id}` computes deal status.
- `GET/POST/DELETE /api/v1/wish_lists` manages the authenticated user's wishlist.
- `GET/POST/DELETE /api/v1/price_alerts` manages the authenticated user's alerts.
- `POST /api/v1/price_alerts/trigger` checks the authenticated user's active alerts.
- `POST /api/v1/advisor/chat` returns advisor answers and product recommendations.

## Crawling & Ingestion
- Python crawlers in `services/crawler/` (Playwright + BeautifulSoup) for CellphoneS, FPT Shop, and Phong Vũ.
- Entry point: `services/crawler/main.py` (cron-safe), invoked via `services/crawler/run_crawler.sh`.
- Crawlers output CSV snapshots to `services/crawler/output/`; backend ingestion remains available through crawler endpoints.
- `services/crawler/main.py` imports all three crawlers, but the checked-in default run enables only Phong Vũ. FPT Shop and CellphoneS calls are currently commented out.
- `services/pipeline/main.py` currently has Stage 1 CSV loading and final persistence stages commented out; the checked-in entry point focuses on schema/Typesense setup and LLM normalization.
- Upload endpoints require `X-API-Key` matching `DEV_API_KEY` in server `.env`.
- Typesense `products` collection is ensured by backend product/search handlers (infix enabled for `normalized_name`, `product_name`).

## Frontend UX
- Tabs: Search/Compare, Trending Deals, Wishlist, Price Alerts.
- Product detail includes platform comparison, seller links, wishlist and alert controls, deal analysis, and a price history chart (Recharts).
- Auth modal supports email/password login/register, forgot password, and Google/GitHub login redirects.
- User session, wishlist, and price-alert state are managed in `UserContext` with optimistic UI updates and backend synchronization.
- Uses Tailwind CSS, Lucide icons, and Motion for transitions.

## Configuration & Secrets
- Server config via `.env` (see `server/.env.example`).
- Key settings: Postgres connection, `DEV_API_KEY`, `TYPESENSE_API_KEY`, `TYPESENSE_HOST`, `TYPESENSE_PORT`, `TYPESENSE_PROTOCOL`, CORS origins, JWT settings, frontend/backend URLs, OAuth credentials, SMTP credentials, and Advisor provider settings.

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
- Server tests are present under `server/tests/` and run with `pytest`.
- Client tests are present under `client/src/**/__tests__/` and run with `npm run test`.
