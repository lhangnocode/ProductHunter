from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.tools.common import product_payload
from app.models.platform_product import PlatformProduct
from app.models.product import Product


class ProductDetailInput(BaseModel):
    product_id: UUID


async def get_product_detail(
    db: AsyncSession,
    product_id: UUID,
) -> dict[str, Any]:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        return {"product_id": product_id, "found": False}
    return {"found": True, "product": product_payload(product, include_offers=True)}
