# Server

FastAPI backend for ProductHunter. Major implemented areas:

- Product search and comparison with Typesense fallback to PostgreSQL.
- Platform and platform-product APIs.
- Crawler ingestion protected by `X-API-Key`.
- Price records, price analysis, and trending deals.
- Email/password auth, refresh tokens, password reset, Google/GitHub OAuth.
- Wishlist and price-alert APIs for authenticated users.
- ProductHunter Advisor chat endpoint.

### Manual run the server (dev)

```bash
#(assuming you are in the root directory of the project)
cd server
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Crawler upload APIs (DEV only)

Set `DEV_API_KEY` in `.env`, then send it in `X-API-Key` header.

- `POST /api/v1/crawler/products`
- `POST /api/v1/crawler/platform-products`
  
Example:

```bash
curl -X POST http://localhost:8000/api/v1/crawler/products \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DEV_API_KEY" \
  -d '{"normalized_name":"iphone 15","slug":"iphone-15","brand":"Apple","category":"phone","main_image_url":"https://example.com/p.jpg"}'
```

### Tests

```bash
pytest
```

Tests live in `server/tests/` and cover auth, crawler ingest, products,
platform products, price records, trending deals, wishlist, price alerts,
security, social auth, Advisor, and integration flows.

### Coverage

`pytest-cov` is included in `requirements.txt`. Run coverage from `server/`:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

This prints missing lines in the terminal, writes the HTML report to
`server/htmlcov/index.html`, and writes the XML report to `server/coverage.xml`.

### Docker Compose

`docker-compose.yml` now includes both `api` and `postgres` (`postgres:16-alpine`) services.

Build default image tag:

```bash
docker compose build
```

Build with a new version tag (`cloud_producthunt:{ver}`):

```bash
IMAGE_TAG=1.0 docker compose build
```

PowerShell:

```powershell
$env:IMAGE_TAG="1.0"; docker compose build
```

Run the stack:

```bash
docker compose up -d
```

Postgres will auto-run `server/db/schema.sql` on first initialization (empty `pg_data` volume) via `/docker-entrypoint-initdb.d`.

If your DB volume already exists and you need to re-run init scripts:

```bash
docker compose down -v
docker compose up -d
```
