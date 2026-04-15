from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, delete
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import selectinload
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

    query = (
        select(PriceAlert)
        .options(selectinload(PriceAlert.product)) 
        .where(
            PriceAlert.user_id == user_id,
            PriceAlert.product_id == alert_in.product_id
        )
    )
    result = await db.execute(query)
    row = result.scalar_one()

    # Trả về dict để khớp hoàn toàn với schema PriceAlertResponse
    return {
        "product_id": row.product_id,
        "target_price": row.target_price,
        "status": row.status,
        "product_name": row.product.normalized_name if row.product else "Sản phẩm",
        "main_image_url": row.product.main_image_url if row.product else None,
    }

async def get_user_alerts(db: AsyncSession, user_id: UUID):
    stmt = (
        select(PriceAlert)
        .options(selectinload(PriceAlert.product)) # Tự động JOIN lấy data product
        .where(PriceAlert.user_id == user_id)
        # Bỏ comment dòng order_by dưới đây nếu model của bạn có trường created_at
        .order_by(PriceAlert.created_at.desc()) 
    )
    
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # 2. Map dữ liệu để trả về theo đúng định dạng của PriceAlertResponse
    alerts = []
    for row in rows:
        alerts.append({
            "product_id": row.product_id,
            "target_price": row.target_price,
            "status": row.status,
            # Lấy thông tin từ bảng product (nếu product tồn tại)
            "product_name": row.product.normalized_name if row.product else "Sản phẩm không xác định",
            "main_image_url": row.product.main_image_url if row.product else None,
        })
        
    return alerts

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

async def remove_price_alert(db: AsyncSession, user_id: UUID, product_id: UUID) -> None:
    """
    Xóa cảnh báo giá của một sản phẩm do người dùng đặt.
    """
    stmt = delete(PriceAlert).where(
        PriceAlert.user_id == user_id,
        PriceAlert.product_id == product_id,
    )
    result = await db.execute(stmt)
    await db.commit()

    # Nếu rowcount == 0 nghĩa là không tìm thấy cảnh báo nào để xóa
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy cảnh báo giá cho sản phẩm này.",
        )