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
