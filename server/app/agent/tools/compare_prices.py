from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.tools.common import product_payload
from app.models.platform_product import PlatformProduct
from app.models.product import Product


class ComparePricesInput(BaseModel):
    product_ids: list[UUID] = Field(..., min_length=1, max_length=5)


async def compare_prices(
    db: AsyncSession,
    product_ids: list[UUID],
) -> dict[str, Any]:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(Product.id.in_(product_ids))
    )
    products = list(result.scalars().unique().all())
    product_map = {product.id: product for product in products}
    ordered = [
        product_payload(product_map[product_id], include_offers=True)
        for product_id in product_ids
        if product_id in product_map
    ]
    return {"products": ordered}
