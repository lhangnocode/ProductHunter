# app/services/price_alert.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from uuid import UUID
from fastapi import BackgroundTasks

from app.models.price_alert import PriceAlert
from app.models.product import Product
from app.models.user import User
from app.schemas.price_alert import PriceAlertCreate
from app.services.email import send_price_drop_email_async 

# ==========================================
# 1. HÀM DÀNH CHO USER (API Đặt ngưỡng giá)
# ==========================================
async def set_price_alert(
    db: AsyncSession,
    user_id: UUID,
    alert_in: PriceAlertCreate
):
    # UPSERT
    stmt = insert(PriceAlert).values(
        user_id=user_id,
        product_id=alert_in.product_id,
        target_price=alert_in.target_price,
        status=0
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'product_id'],
        set_=dict(
            target_price=alert_in.target_price,
            status=0
        )
    )

    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(PriceAlert).where(
            PriceAlert.user_id == user_id,
            PriceAlert.product_id == alert_in.product_id
        )
    )

    return result.scalar_one()

# ==========================================
#! 2. HÀM DÀNH CHO HỆ THỐNG (Crawler gọi để check)
# ==========================================
async def check_and_trigger_alerts(
    db: AsyncSession, 
    product_id: UUID, 
    current_lowest_price: float, 
    bg_tasks: BackgroundTasks
):
    # 1. Tìm alerts thỏa mãn (Dùng 문 pháp Async của SQLAlchemy 2.0)
    stmt_alert = select(PriceAlert).where(
        PriceAlert.product_id == product_id,
        PriceAlert.status == 0, # Đang Active
        PriceAlert.target_price >= current_lowest_price
    )
    result_alert = await db.execute(stmt_alert)
    triggered_alerts = result_alert.scalars().all()

    if not triggered_alerts:
        return

    # 2. Lấy thông tin Product
    stmt_product = select(Product).where(Product.id == product_id)
    result_product = await db.execute(stmt_product)
    product = result_product.scalar_one_or_none()

    if not product: return

    for alert in triggered_alerts:
        # Lấy thông tin User để lấy email
        stmt_user = select(User).where(User.id == alert.user_id)
        result_user = await db.execute(stmt_user)
        user = result_user.scalar_one_or_none()

        if user:
            # 3. Add tác vụ gửi mail vào Background
            bg_tasks.add_task(
                send_price_drop_email_async,
                to_email=user.email,
                product_name=product.normalized_name,
                current_price=current_lowest_price,
                target_price=alert.target_price
            )
            
            # 4. Cập nhật trạng thái alert
            alert.status = 1
    
    # 5. Commit lưu thay đổi status
    await db.commit()