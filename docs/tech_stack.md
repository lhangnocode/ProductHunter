### Project context

A Micro-SaaS for user to find better price of a product (Tech products) by comparing prices across different e-commerce platforms (Shopee, Lazada, Amazon, TaoBao, TiKi etc.).

### Tech stack

#### Web services
- **Backend**: Python (FastAPI)
- **Frontend**: React/Next.js
- **Database**: PostgreSQL with Search extension Typesense (for product search) or Elasticsearch

#### Crawling services
- **Crawler**: Python (Scrapy or Playwright)
- **Task scheduling**: Cron jobs (Linux)

#### Deployment
- **Containerization**: Docker
- **Provider**: 
    - On-premises with Tailscale Tunneling (Backend and Crawlers)
    - Frontend hosted on Vercel (Free hosting)

### Strategy
- The SaaS will only support tech products to narrow down the scope and focus on a specific market.
- Data collection will be done through 2 strategy:
    - Crawling: Regularly scheduled crawlers will fetch product data from various e-commerce platforms.
    - Data from users: Extension that reads product information from the user's browser and sends it to the backend for price comparison. (May require user permission and compliance with privacy policies).
- The backend will provide APIs for the frontend to fetch product information and price comparisons.
- The producst name will be encoded for searching by using techniques like TF-IDF or word embeddings to improve search accuracy and relevance.
    - Product name -> Normalization (lowercase, remove special characters) -> Vectorization. For searching
    - Product find -> Distance vectorization -> Sort by distance: Threshold 0.8. Cosine similarity or Euclidean distance.