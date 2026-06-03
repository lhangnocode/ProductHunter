from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.common import to_float
from app.models.price_record import PriceRecord

PRICE_HISTORY_WINDOW_DAYS = 90
TREND_FALLING_THRESHOLD_PCT = 2.0
TREND_RISING_THRESHOLD_PCT = 2.0


class PriceHistoryInput(BaseModel):
    platform_product_ids: list[UUID] = Field(..., min_length=1, max_length=10)


def _trend_label(window_records: int, baseline_avg: float, recent_avg: float) -> str:
    if window_records < 2 or baseline_avg is None or recent_avg is None or baseline_avg <= 0:
        return "flat"
    delta = (recent_avg - baseline_avg) / baseline_avg * 100.0
    if delta <= -TREND_FALLING_THRESHOLD_PCT:
        return "falling"
    if delta >= TREND_RISING_THRESHOLD_PCT:
        return "rising"
    return "flat"


async def get_price_history(
    db: AsyncSession,
    platform_product_ids: list[UUID],
) -> dict[str, Any]:
    if not platform_product_ids:
        return {"price_history": []}

    cutoff = datetime.now(timezone.utc) - timedelta(days=PRICE_HISTORY_WINDOW_DAYS)

    window_result = await db.execute(
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price),
            func.avg(PriceRecord.price),
            func.max(PriceRecord.price),
            func.count(PriceRecord.id),
        )
        .where(PriceRecord.platform_product_id.in_(platform_product_ids))
        .where(PriceRecord.recorded_at >= cutoff)
        .group_by(PriceRecord.platform_product_id)
    )
    window_rows = {
        row[0]: {
            "min_90d": to_float(row[1]),
            "avg_90d": to_float(row[2]),
            "max_90d": to_float(row[3]),
            "records_90d": int(row[4] or 0),
        }
        for row in window_result.all()
    }

    all_result = await db.execute(
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price),
            func.avg(PriceRecord.price),
        )
        .where(PriceRecord.platform_product_id.in_(platform_product_ids))
        .group_by(PriceRecord.platform_product_id)
    )
    all_rows = {
        row[0]: {
            "min_price": to_float(row[1]),
            "avg_price": to_float(row[2]),
        }
        for row in all_result.all()
    }

    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    recent_result = await db.execute(
        select(
            PriceRecord.platform_product_id,
            func.avg(PriceRecord.price),
        )
        .where(PriceRecord.platform_product_id.in_(platform_product_ids))
        .where(PriceRecord.recorded_at >= recent_cutoff)
        .group_by(PriceRecord.platform_product_id)
    )
    recent_rows = {row[0]: to_float(row[1]) for row in recent_result.all()}

    summaries: list[dict[str, Any]] = []
    for platform_product_id in platform_product_ids:
        window = window_rows.get(platform_product_id, {})
        baseline = all_rows.get(platform_product_id, {})
        recent_avg = recent_rows.get(platform_product_id)
        baseline_avg = baseline.get("avg_price") or window.get("avg_90d")
        trend = _trend_label(window.get("records_90d", 0) or 0, baseline_avg, recent_avg)

        min_90d = window.get("min_90d")
        current_vs_min_pct: float | None = None
        # `current_price` is unknown at this layer (offer-level), so caller can compute.
        # Expose the raw `min_90d` and `avg_90d` for the composer to combine with offers.
        summaries.append(
            {
                "platform_product_id": platform_product_id,
                "min_price": baseline.get("min_price"),
                "avg_price": baseline.get("avg_price"),
                "min_90d": min_90d,
                "avg_90d": window.get("avg_90d"),
                "max_90d": window.get("max_90d"),
                "records_90d": window.get("records_90d", 0),
                "trend": trend,
                "current_vs_min_pct": current_vs_min_pct,
            }
        )

    return {"price_history": summaries}
