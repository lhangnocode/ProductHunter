### Project context

A Micro-SaaS for users to find better prices for tech products by comparing listings across multiple e-commerce platforms.

### Tech stack

#### Web services
- **Backend**: Python (FastAPI + async SQLAlchemy)
- **Frontend**: React (Vite)
- **Database**: PostgreSQL
- **Search**: Typesense (`products` collection with infix-enabled fields)

#### Crawling services
- **Crawler**: Python (Playwright + BeautifulSoup)
- **Supported crawler implementations**: CellphoneS, FPT Shop, Phong Vũ
- **Task scheduling**: Cron jobs (Linux) via `services/crawler/run_crawler.sh`

#### Deployment
- **Containerization**: Docker Compose (API + Postgres + Typesense)
- **Provider**:
    - On-premises with Tailscale tunneling (backend and crawlers)
    - Frontend hosted separately (static/Vite build)

### Strategy
- The SaaS focuses on tech products to narrow scope and improve catalog quality.
- Data collection is currently crawler-driven with scheduled runs and API ingestion.
- The backend exposes APIs for search and comparison, using Typesense for ranking with a Postgres fallback.
- The browser extension exists as a Plasmo project; production integration remains an optional roadmap item.
- Authentication, wishlist, price alerts, trending deals, price analysis, and Advisor chat are implemented in the backend and frontend.
