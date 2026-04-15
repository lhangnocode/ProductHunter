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
    Phân tích mức độ giảm giá dựa trên lịch sử trong DB.
    Trả về: { status: str, label: str, lowest_ever: float, avg_30days: float }
    """
    
    # 1. Tìm giá thấp nhất lịch sử
    stmt_min = select(func.min(PriceRecord.price)).where(
        PriceRecord.platform_product_id == platform_product_id
    )
    res_min = await db.execute(stmt_min)
    lowest_ever = res_min.scalar()
    
    # Nếu chưa có lịch sử, lấy giá hiện tại làm mốc
    if lowest_ever is None:
        lowest_ever = current_price

    # 2. Tính giá trung bình 30 ngày gần nhất
    utc_now = datetime.now(timezone.utc)
    thirty_days_ago = utc_now - timedelta(days=30)
    stmt_avg = select(func.avg(PriceRecord.price)).where(
        and_(
            PriceRecord.platform_product_id == platform_product_id,
            PriceRecord.recorded_at >= thirty_days_ago
        )
    )
    res_avg = await db.execute(stmt_avg)
    avg_30days = res_avg.scalar()

    # Nếu không có dữ liệu 30 ngày, lấy giá hiện tại làm mốc
    if avg_30days is None:
        avg_30days = current_price
    
    avg_30days = float(avg_30days)
    lowest_ever = float(lowest_ever)

    # 3. Logic phân cấp theo ảnh yêu cầu
    status = "stable"
    label = "Giá ổn định"

    # Cực hời: Giá HT <= Thấp nhất lịch sử
    if current_price <= lowest_ever and current_price < avg_30days:
        status = "extreme"
        label = "Rẻ kỷ lục"
    
    # Ảo / Chiêu trò: Giá HT >= TB 30 ngày (Dù có tag giảm giá)
    elif current_price >= avg_30days and original_price > current_price:
        status = "fake"
        label = "Khuyến mãi ảo"
    
    # Giảm tốt: Giá HT < TB 30 ngày
    elif current_price < avg_30days:
        status = "good"
        label = "Giá tốt"
        
    # Giảm nhẹ: Giá HT < Giá niêm yết (Và không rơi vào các trường hợp trên)
    elif original_price > current_price:
        status = "slight"
        label = "Có giảm"

    return {
        "deal_status": status,
        "deal_label": label,
        "lowest_ever_price": lowest_ever,
        "avg_price_30d": avg_30days,
        "current_price": current_price
    }