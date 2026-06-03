from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.common import to_float
from app.models.price_record import PriceRecord


class PriceHistoryInput(BaseModel):
    platform_product_ids: list[UUID] = Field(..., min_length=1, max_length=10)


async def get_price_history(
    db: AsyncSession,
    platform_product_ids: list[UUID],
) -> dict[str, Any]:
    result = await db.execute(
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price),
            func.avg(PriceRecord.price),
        )
        .where(PriceRecord.platform_product_id.in_(platform_product_ids))
        .group_by(PriceRecord.platform_product_id)
    )
    summaries = [
        {
            "platform_product_id": row[0],
            "min_price": to_float(row[1]),
            "avg_price": to_float(row[2]),
        }
        for row in result.all()
    ]
    return {"price_history": summaries}
