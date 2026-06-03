from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.common import product_payload
from app.handlers.handler_product import search_product


class SearchProductsInput(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


async def search_products(
    db: AsyncSession,
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    products, total = await search_product(query=query, db=db, limit=limit, page=1)
    return {
        "query": query,
        "total_results": total,
        "products": [
            product_payload(product, include_offers=True)
            for product in products[:limit]
        ],
    }
