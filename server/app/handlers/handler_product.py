import asyncio
import os
from typing import List, Optional
from uuid import UUID

import typesense
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from app.schemas.crawler import ProductIngestRequest


def _build_typesense_client() -> typesense.Client:
    api_key = settings.TYPESENSE_API_KEY or os.getenv("TYPESENSE_API_KEY", "")
    if not api_key:
        raise RuntimeError("TYPESENSE_API_KEY is not configured")

    host = os.getenv("TYPESENSE_HOST")
    if not host:
        host = "typesense" if settings.POSTGRES_HOST == "postgres" else "localhost"
    port = int(os.getenv("TYPESENSE_PORT", "8108"))
    protocol = os.getenv("TYPESENSE_PROTOCOL", "http")

    return typesense.Client(
        {
            "nodes": [
                {
                    "host": host,
                    "port": port,
                    "protocol": protocol,
                }
            ],
            "api_key": api_key,
            "connection_timeout_seconds": 2,
        }
    )


async def upsert_product(
    payload: ProductIngestRequest,
    db: AsyncSession,
    typesense_client: Optional[typesense.Client] = None,
) -> Product:
    stmt = select(Product).where(Product.slug == payload.slug)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        product = Product(**payload.model_dump())
        db.add(product)
    else:
        for field, value in payload.model_dump().items():
            setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    client = typesense_client or _build_typesense_client()
    document = {
        "id": str(product.id),
        "normalized_name": product.normalized_name,
        "slug": product.slug,
    }
    await asyncio.to_thread(
        client.collections["products"].documents.upsert,
        document,
    )
    return product


async def search_product(
    query: str,
    db: AsyncSession,
    limit: int = 20,
    page: int = 1,
    typesense_client: Optional[typesense.Client] = None,
) -> List[Product]:
    if not query or not query.strip():
        return []

    client = typesense_client or _build_typesense_client()
    search_params = {
        "q": query.strip(),
        "query_by": "normalized_name,slug",
        "query_by_weights": "8,2",
        "num_typos": 2,
        "min_len_1typo": 4,
        "min_len_2typo": 7,
        "typo_tokens_threshold": 1,
        "infix": "always",
        "drop_tokens_threshold": 2,
        "prefix": True,
        "per_page": limit,
        "page": page,
    }

    search_result = await asyncio.to_thread(
        client.collections["products"].documents.search,
        search_params,
    )
    hits = search_result.get("hits", [])

    product_ids: List[UUID] = []
    for hit in hits:
        doc = hit.get("document", {})
        raw_id = doc.get("id")
        if not raw_id:
            continue
        try:
            product_ids.append(UUID(raw_id))
        except ValueError:
            continue

    if not product_ids:
        return []

    ordering = case(
        {product_id: index for index, product_id in enumerate(product_ids)},
        value=Product.id,
    )

    stmt = (
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(Product.id.in_(product_ids))
        .order_by(ordering)
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()
