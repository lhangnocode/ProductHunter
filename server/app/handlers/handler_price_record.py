from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.models.price_record import PriceRecord
from typing import Dict, Any


async def analyze_price_status(
    db: AsyncSession,
    platform_product_id: str,
    current_price: float,
    original_price: float
) -> Dict[str, Any]:
    """
    Phân tích chất lượng deal dựa trên lịch sử giá.

    Quy tắc:
    - extreme: giá thấp nhất lịch sử + thấp hơn TB 60 ngày
    - good: thấp hơn đáng kể so với TB 60 ngày
    - fake: giá cao hơn đáng kể so với TB 60 ngày nhưng vẫn treo giảm giá
    - slight: có giảm nhẹ so với original price
    - stable: bình thường
    """

    # ============================================================
    # 1. Giá thấp nhất lịch sử
    # ============================================================

    stmt_min = select(func.min(PriceRecord.price)).where(
        PriceRecord.platform_product_id == platform_product_id
    )

    res_min = await db.execute(stmt_min)
    lowest_ever = res_min.scalar()

    # Nếu chưa có lịch sử
    if lowest_ever is None:
        lowest_ever = current_price

    lowest_ever = float(lowest_ever)

    # ============================================================
    # 2. Giá trung bình 60 ngày gần nhất
    # ============================================================

    utc_now = datetime.now(timezone.utc)
    sixty_days_ago = utc_now - timedelta(days=60)

    stmt_avg = select(func.avg(PriceRecord.price)).where(
        and_(
            PriceRecord.platform_product_id == platform_product_id,
            PriceRecord.recorded_at >= sixty_days_ago
        )
    )

    res_avg = await db.execute(stmt_avg)
    avg_60days = res_avg.scalar()

    # Nếu không có dữ liệu 60 ngày
    if avg_60days is None:
        avg_60days = current_price

    avg_60days = float(avg_60days)

    # ============================================================
    # 3. Tính phần trăm giảm giá
    # ============================================================

    discount_percent = 0.0

    if original_price and original_price > 0:
        discount_percent = (
            (original_price - current_price) / original_price
        )

    # ============================================================
    # 4. Logic phân loại deal
    # ============================================================

    status = "stable"
    label = "Giá ổn định"

    # ------------------------------------------------------------
    # EXTREME
    # Giá hiện tại thấp nhất lịch sử
    # và thấp hơn trung bình 60 ngày
    # ------------------------------------------------------------

    if (
        current_price <= lowest_ever
        and current_price < avg_60days
    ):
        status = "extreme"
        label = "Rẻ kỷ lục"

    # ------------------------------------------------------------
    # GOOD
    # Rẻ hơn ít nhất 5% so với TB 60 ngày
    # ------------------------------------------------------------

    elif current_price < avg_60days * 0.95:
        status = "good"
        label = "Giá tốt"

    # ------------------------------------------------------------
    # FAKE
    # Giá cao hơn ít nhất 10% so với TB 60 ngày
    # nhưng vẫn treo giảm giá mạnh
    # ------------------------------------------------------------

    elif (
        current_price >= avg_60days * 1.10
        and discount_percent >= 0.15
    ):
        status = "fake"
        label = "Khuyến mãi ảo"

    # ------------------------------------------------------------
    # SLIGHT
    # Chỉ giảm nhẹ
    # ------------------------------------------------------------

    elif original_price > current_price:
        status = "slight"
        label = "Có giảm"

    # ============================================================
    # 5. Return
    # ============================================================

    return {
        "deal_status": status,
        "deal_label": label,
        "lowest_ever_price": lowest_ever,
        "avg_price_60d": avg_60days,
        "current_price": current_price,
        "discount_percent": round(discount_percent * 100, 2)
    }