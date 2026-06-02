from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, delete, func
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import selectinload
from app.models.price_alert import PriceAlert
from app.models.platform_product import PlatformProduct
from app.schemas.price_alert import PriceAlertCreate
from app.services.email import send_price_drop_email_async 

FREE_PLAN_PRICE_ALERT_LIMIT = 5

# ==========================================
# 1. HÀM DÀNH CHO USER (API Đặt ngưỡng giá)
# ==========================================
async def set_price_alert(
    db: AsyncSession,
    user_id: UUID,
    alert_in: PriceAlertCreate,
    user_plan: int = 0,
):
    existing_stmt = select(PriceAlert.id).where(
        PriceAlert.user_id == user_id,
        PriceAlert.product_id == alert_in.product_id,
    )
    existing_result = await db.execute(existing_stmt)
    existing_alert_id = existing_result.scalar_one_or_none()

    if user_plan == 0 and existing_alert_id is None:
        count_stmt = select(func.count(PriceAlert.id)).where(PriceAlert.user_id == user_id)
        alert_count = await db.scalar(count_stmt) or 0
        if alert_count >= FREE_PLAN_PRICE_ALERT_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Free plan users can only create price alerts for up to 5 products. "
                    "Upgrade to Pro for unlimited alerts."
                ),
            )

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

async def _get_current_lowest_price(db: AsyncSession, product_id: UUID):
    stmt_lowest_price = select(func.min(PlatformProduct.current_price)).where(
        PlatformProduct.product_id == product_id,
        PlatformProduct.in_stock.is_(True),
        PlatformProduct.current_price.is_not(None),
    )
    result_lowest_price = await db.execute(stmt_lowest_price)
    return result_lowest_price.scalar_one_or_none()


async def check_and_trigger_user_alerts(
    db: AsyncSession,
    user_id: UUID,
    bg_tasks: BackgroundTasks,
    product_id: UUID | None = None,
):
    stmt_alerts = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.user),
        )
        .where(
            PriceAlert.user_id == user_id,
            PriceAlert.status == 0,
        )
    )

    if product_id is not None:
        stmt_alerts = stmt_alerts.where(PriceAlert.product_id == product_id)

    result_alerts = await db.execute(stmt_alerts)
    active_alerts = result_alerts.scalars().all()

    checked_products = 0
    triggered_alerts = 0
    skipped_without_price = 0

    for alert in active_alerts:
        current_lowest_price = await _get_current_lowest_price(db, alert.product_id)
        if current_lowest_price is None:
            skipped_without_price += 1
            continue

        checked_products += 1
        if alert.target_price < current_lowest_price:
            continue

        if alert.user and alert.product:
            bg_tasks.add_task(
                send_price_drop_email_async,
                to_email=alert.user.email,
                product_name=alert.product.normalized_name,
                current_price=current_lowest_price,
                target_price=alert.target_price,
            )

        alert.status = 1
        triggered_alerts += 1

    await db.commit()
    return {
        "checked_products": checked_products,
        "triggered_alerts": triggered_alerts,
        "skipped_without_price": skipped_without_price,
    }

# ==========================================
#! 2. HÀM DÀNH CHO HỆ THỐNG (Crawler gọi để check)
# ==========================================
async def check_and_trigger_alerts(
    db: AsyncSession,
    product_id: UUID,
    bg_tasks: BackgroundTasks
):
    current_lowest_price = await _get_current_lowest_price(db, product_id)

    if current_lowest_price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy giá hiện tại còn hàng cho sản phẩm này.",
        )

    stmt_alert = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.user),
        )
        .where(
            PriceAlert.product_id == product_id,
            PriceAlert.status == 0, # Đang Active
            PriceAlert.target_price >= current_lowest_price
        )
    )
    result_alert = await db.execute(stmt_alert)
    triggered_alerts = result_alert.scalars().all()

    if not triggered_alerts:
        return float(current_lowest_price)

    for alert in triggered_alerts:
        if alert.user and alert.product:
            # 3. Add tác vụ gửi mail vào Background
            bg_tasks.add_task(
                send_price_drop_email_async,
                to_email=alert.user.email,
                product_name=alert.product.normalized_name,
                current_price=current_lowest_price,
                target_price=alert.target_price
            )
            
        # 4. Cập nhật trạng thái alert
        alert.status = 1
    
    # 5. Commit lưu thay đổi status
    await db.commit()
    return float(current_lowest_price)

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
