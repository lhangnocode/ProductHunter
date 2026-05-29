# Architecture

ProductHunter is split into four main parts:

- `client/`: Vite + React frontend.
- `server/`: FastAPI API, PostgreSQL models, Typesense-backed search, authentication, wishlist, price alerts, price records, trending deals, and Advisor.
- `services/crawler/`: Playwright + BeautifulSoup crawlers for CellphoneS, FPT Shop, and Phong Vũ.
- `services/pipeline/`: CSV staging, normalization, product resolution, persistence, and Typesense sync utilities.

## Runtime Topology

```text
CellphoneS crawler ┐
FPT Shop crawler   ├─> services/crawler/output/*.csv ─┐
Phong Vu crawler   ┘                                  │
                                                       v
                                           services/pipeline/
                                                       │
                                                       v
Frontend ───────────────> FastAPI API ─────────> PostgreSQL
   │                         │                    price/product data
   │                         v
   └──────────────────> Typesense
                         product search index
```

Current implementation note: the crawler writes CSV snapshots. The pipeline has
utilities for staging, normalization, product resolution, persistence, and
Typesense sync, but the checked-in `services/pipeline/main.py` currently has the
CSV load and final persistence stages commented out.

## Crawler Flow

`services/crawler/main.py` imports:

- `CellphonesCrawler` from `services/crawler/impl/cellphones/crawler_cellphones.py`
- `FPTShopCrawler` from `services/crawler/impl/fpt/crawler_fptshop.py`
- `PhongVuCrawler` from `services/crawler/impl/phongvu/crawler_phongvu.py`

Current checked-in default: only `PhongVuCrawler` is enabled in `main.py`; the
FPT Shop and CellphoneS calls are commented out. The codebase still contains all
three crawler implementations.

Platform IDs used by crawler/server data:

| Platform | ID |
|---|---:|
| CellphoneS | 9 in `services/crawler/impl/cellphones/crawler_cellphones.py`; 6 in `services/crawler/core/define/platform_type.py`; 4 in `services/pipeline/define/platform.py`; 9 in `services/pipeline/config.py` CSV registry |
| FPT Shop | 7 |
| Phong Vũ | 8 |

The CellphoneS ID differs across crawler and pipeline definitions and should be
confirmed before relying on automated cross-stage mapping.

## API Flow

The frontend calls `CONFIG.API_URL` from `client/src/config.ts`. Main API groups:

- `/api/v1/auth`: register, login, refresh, profile, password reset, Google/GitHub OAuth.
- `/api/v1/products`: search, list, searchAll, compare.
- `/api/v1/platform_products`: search/list platform offers and trending deals.
- `/api/v1/price_record`: price history and price analysis.
- `/api/v1/wish_lists`: authenticated wishlist management.
- `/api/v1/price_alerts`: authenticated alert management and user-scoped trigger.
- `/api/v1/crawler`: DEV API key protected product and platform-product ingestion.
- `/api/v1/advisor`: Advisor chat.

## Price Alert Flow

Users create or update alerts from product detail. The frontend stores alert state
in `UserContext`, performs optimistic UI updates, and syncs with
`/api/v1/price_alerts`.

`POST /api/v1/price_alerts/trigger` checks active alerts for the authenticated
user, computes the lowest in-stock `platform_products.current_price`, queues
price-drop email tasks, and marks matching alerts as triggered. Automatic crawler
invocation of this trigger is not yet implemented.

## Product Detail Flow

Search results open `ProductDetail`, which fetches comparison groups from
`/api/v1/products/compare`, derives platform offers, fetches price records from
`/api/v1/price_record/price-records/{platform_product_id}`, and fetches deal
analysis from `/api/v1/price_record/price-analysis/{platform_product_id}`.
