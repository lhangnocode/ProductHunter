# Server

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
