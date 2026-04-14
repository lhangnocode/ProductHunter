from typing import List
from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.price_alert import PriceAlertCreate, PriceAlertResponse
from app.services import price_alert as price_alert_service
from app.models.user import User

router = APIRouter()

# Schema dùng riêng cho API Trigger
class TriggerAlertInput(BaseModel):
    product_id: UUID
    current_lowest_price: float


# 1. API Tạo/Cập nhật cảnh báo (Cũ - Giữ nguyên)
@router.post("/", response_model=PriceAlertResponse)
async def create_or_update_alert(
    alert_in: PriceAlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Đặt ngưỡng giá theo dõi cho một sản phẩm.
    """
    return await price_alert_service.set_price_alert(
        db,
        current_user.id,
        alert_in
    )


# 2. API Lấy danh sách cảnh báo của bản thân
@router.get("/", response_model=List[PriceAlertResponse])
async def get_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách các cảnh báo giá mà user đang đăng nhập đã đặt.
    """
    return await price_alert_service.get_user_alerts(db, current_user.id)

# 3. API Xóa cảnh báo giá
@router.delete("/{product_id}")
async def delete_price_alert(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xóa cảnh báo giá của một sản phẩm.
    """
    await price_alert_service.remove_price_alert(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )
    return {"message": "Đã xóa cảnh báo giá thành công"}

# 4. API Kích hoạt kiểm tra giá (Crawler hoặc Admin gọi)
@router.post("/trigger")
async def trigger_price_check(
    trigger_in: TriggerAlertInput,
    bg_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    # Tùy chọn: Bạn có thể yêu cầu user đăng nhập để gọi API này, 
    # Hoặc thay bằng Depends(get_api_key) nếu API này chỉ dành cho Bot/Crawler
    current_user: User = Depends(get_current_user) 
):
    """
    Kích hoạt hệ thống kiểm tra và gửi email cảnh báo giá.
    (Giả lập việc Crawler vừa cào được giá mới và gọi API này).
    """
    await price_alert_service.check_and_trigger_alerts(
        db=db,
        product_id=trigger_in.product_id,
        current_lowest_price=trigger_in.current_lowest_price,
        bg_tasks=bg_tasks
    )
    
    return {
        "status": "success",
        "message": f"Đã chạy tiến trình kiểm tra giá cho product_id: {trigger_in.product_id}",
        "current_lowest_price": trigger_in.current_lowest_price
    }