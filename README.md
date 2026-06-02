# ProductHunter

ProductHunter is a tech-product price tracking and comparison system. 

## Repository Layout
- `client/`: Vite + React + TypeScript frontend.
- `server/`: FastAPI backend with async SQLAlchemy, PostgreSQL, Typesense integration, auth, wishlist, price alerts, price records, trending deals, and Advisor APIs.
- `services/`: crawler and pipeline code. Current crawler implementations cover CellphoneS, FPT Shop, and Phong Vũ.
- `product-hunter-extension/`: Plasmo browser extension project.
- `docs/`: project specs, tech stack, and implementation notes.

## Local Development

Server:

```bash
cd server
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Client:

```bash
cd client
npm install
npm run dev
```

Crawler:

```bash
bash services/crawler/run_crawler.sh
```

Tests:

```bash
cd server && pytest
cd client && npm run test
```
