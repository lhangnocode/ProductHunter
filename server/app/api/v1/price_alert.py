from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.price_alert import PriceAlertCreate, PriceAlertResponse
from app.services import price_alert as price_alert_service
from app.models.user import User

router = APIRouter()


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