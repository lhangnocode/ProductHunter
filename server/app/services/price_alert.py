from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, delete, func
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import selectinload
from app.models.price_alert import PriceAlert
from app.models.platform_product import PlatformProduct
from app.schemas.price_alert import PriceAlertCreate
from app.services.email import send_price_drop_email_async
from app.services.push_notifications import send_price_alert_push

FREE_PLAN_PRICE_ALERT_LIMIT = 5

EmailSender = Callable[..., Awaitable[None]]


@dataclass
class _TriggeredAlertNotification:
    user_id: UUID
    user_email: str | None
    product_id: UUID
    platform_product_id: UUID
    product_name: str
    target_price: Decimal
    current_price: Decimal


def _notification_product_name(alert: PriceAlert) -> str:
    if alert.platform_product and alert.platform_product.raw_name:
        return alert.platform_product.raw_name
    if alert.product:
        return alert.product.normalized_name
    return "Product"


async def _dispatch_triggered_notifications(
    db: AsyncSession,
    notifications: list[_TriggeredAlertNotification],
    bg_tasks: BackgroundTasks | None,
    email_sender: EmailSender = send_price_drop_email_async,
) -> dict[str, int]:
    email_queued = 0
    fcm_sent = 0
    invalid_tokens = 0

    for notification in notifications:
        if notification.user_email:
            email_kwargs = {
                "to_email": notification.user_email,
                "product_name": notification.product_name,
                "current_price": notification.current_price,
                "target_price": notification.target_price,
            }
            if bg_tasks is not None:
                bg_tasks.add_task(email_sender, **email_kwargs)
            else:
                await email_sender(**email_kwargs)
            email_queued += 1

        fcm_result = await send_price_alert_push(
            db=db,
            user_id=notification.user_id,
            product_id=notification.product_id,
            platform_product_id=notification.platform_product_id,
            product_name=notification.product_name,
            target_price=notification.target_price,
            current_price=notification.current_price,
        )
        fcm_sent += fcm_result["fcm_sent"]
        invalid_tokens += fcm_result["invalid_tokens"]

    return {
        "email_queued": email_queued,
        "fcm_sent": fcm_sent,
        "invalid_tokens": invalid_tokens,
    }

# ==========================================
# 1. HÀM DÀNH CHO USER (API Đặt ngưỡng giá)
# ==========================================
async def _resolve_platform_product(
    db: AsyncSession,
    product_id: UUID | None,
    platform_product_id: UUID | None,
) -> PlatformProduct:
    stmt = select(PlatformProduct).options(selectinload(PlatformProduct.product))
    if platform_product_id is not None:
        stmt = stmt.where(PlatformProduct.id == platform_product_id)
    elif product_id is not None:
        stmt = (
            stmt.where(PlatformProduct.product_id == product_id)
            .order_by(PlatformProduct.current_price.asc(), PlatformProduct.id.desc())
            .limit(1)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="platform_product_id is required",
        )

    result = await db.execute(stmt)
    platform_product = result.scalar_one_or_none()
    if platform_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform product not found",
        )
    return platform_product


def _alert_response(row: PriceAlert) -> dict:
    platform_product = row.platform_product
    product = row.product
    return {
        "product_id": row.product_id,
        "platform_product_id": row.platform_product_id,
        "target_price": row.target_price,
        "status": row.status,
        "product_name": (
            platform_product.raw_name
            if platform_product and platform_product.raw_name
            else product.normalized_name if product else "Sản phẩm"
        ),
        "main_image_url": product.main_image_url if product else None,
        "current_price": (
            float(platform_product.current_price)
            if platform_product and platform_product.current_price is not None
            else None
        ),
    }


async def set_price_alert(
    db: AsyncSession,
    user_id: UUID,
    alert_in: PriceAlertCreate,
    user_plan: int = 0,
):
    platform_product = await _resolve_platform_product(
        db,
        product_id=alert_in.product_id,
        platform_product_id=alert_in.platform_product_id,
    )

    existing_stmt = select(PriceAlert.id).where(
        PriceAlert.user_id == user_id,
        PriceAlert.platform_product_id == platform_product.id,
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

    alert_stmt = (
        select(PriceAlert)
        .where(
            PriceAlert.user_id == user_id,
            PriceAlert.platform_product_id == platform_product.id,
        )
    )
    alert_result = await db.execute(alert_stmt)
    alert = alert_result.scalar_one_or_none()

    if alert is None:
        alert = PriceAlert(
            user_id=user_id,
            product_id=platform_product.product_id,
            platform_product_id=platform_product.id,
            target_price=alert_in.target_price,
            status=0,
        )
        db.add(alert)
    else:
        alert.target_price = alert_in.target_price
        alert.status = 0

    await db.commit()

    query = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.platform_product),
        )
        .where(
            PriceAlert.user_id == user_id,
            PriceAlert.platform_product_id == platform_product.id
        )
    )
    result = await db.execute(query)
    row = result.scalar_one()

    return _alert_response(row)

async def get_user_alerts(db: AsyncSession, user_id: UUID):
    stmt = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.platform_product),
        )
        .where(PriceAlert.user_id == user_id)
        # Bỏ comment dòng order_by dưới đây nếu model của bạn có trường created_at
        .order_by(PriceAlert.created_at.desc()) 
    )
    
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [_alert_response(row) for row in rows]

async def _get_current_lowest_price(db: AsyncSession, product_id: UUID):
    stmt_lowest_price = select(func.min(PlatformProduct.current_price)).where(
        PlatformProduct.product_id == product_id,
        PlatformProduct.in_stock.is_(True),
        PlatformProduct.current_price.is_not(None),
    )
    result_lowest_price = await db.execute(stmt_lowest_price)
    return result_lowest_price.scalar_one_or_none()


async def _get_current_platform_price(db: AsyncSession, platform_product_id: UUID):
    stmt = select(PlatformProduct.current_price).where(
        PlatformProduct.id == platform_product_id,
        PlatformProduct.in_stock.is_(True),
        PlatformProduct.current_price.is_not(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def check_and_trigger_user_alerts(
    db: AsyncSession,
    user_id: UUID,
    bg_tasks: BackgroundTasks,
    product_id: UUID | None = None,
    platform_product_id: UUID | None = None,
):
    stmt_alerts = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.user),
            selectinload(PriceAlert.platform_product),
        )
        .where(
            PriceAlert.user_id == user_id,
            PriceAlert.status == 0,
        )
    )

    if product_id is not None:
        stmt_alerts = stmt_alerts.where(PriceAlert.product_id == product_id)
    if platform_product_id is not None:
        stmt_alerts = stmt_alerts.where(PriceAlert.platform_product_id == platform_product_id)

    result_alerts = await db.execute(stmt_alerts)
    active_alerts = result_alerts.scalars().all()

    result = await _trigger_alert_rows(db, active_alerts)
    notification_stats = await _dispatch_triggered_notifications(
        db,
        result.pop("notifications"),
        bg_tasks,
    )
    return {**result, **notification_stats}


async def _trigger_alert_rows(
    db: AsyncSession,
    active_alerts: list[PriceAlert],
) -> dict:
    checked_products = 0
    triggered_alerts = 0
    skipped_without_price = 0
    notifications: list[_TriggeredAlertNotification] = []

    for alert in active_alerts:
        current_price = await _get_current_platform_price(db, alert.platform_product_id)
        if current_price is None:
            skipped_without_price += 1
            continue

        checked_products += 1
        if alert.target_price < current_price:
            continue

        if alert.user_id and alert.product_id and alert.platform_product_id:
            notifications.append(
                _TriggeredAlertNotification(
                    user_id=alert.user_id,
                    user_email=alert.user.email if alert.user else None,
                    product_id=alert.product_id,
                    platform_product_id=alert.platform_product_id,
                    product_name=_notification_product_name(alert),
                    current_price=current_price,
                    target_price=alert.target_price,
                )
            )

        alert.status = 1
        triggered_alerts += 1

    await db.commit()
    return {
        "checked_products": checked_products,
        "triggered_alerts": triggered_alerts,
        "skipped_without_price": skipped_without_price,
        "notifications": notifications,
    }


async def check_and_trigger_system_alerts(
    db: AsyncSession,
    bg_tasks: BackgroundTasks | None = None,
    email_sender: EmailSender = send_price_drop_email_async,
) -> dict[str, int]:
    stmt_alerts = (
        select(PriceAlert)
        .options(
            selectinload(PriceAlert.product),
            selectinload(PriceAlert.user),
            selectinload(PriceAlert.platform_product),
        )
        .where(PriceAlert.status == 0)
    )
    result_alerts = await db.execute(stmt_alerts)
    active_alerts = result_alerts.scalars().all()

    result = await _trigger_alert_rows(db, active_alerts)
    notifications = result.pop("notifications")
    notification_stats = await _dispatch_triggered_notifications(
        db,
        notifications,
        bg_tasks,
        email_sender,
    )
    return {**result, **notification_stats}

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
            selectinload(PriceAlert.platform_product),
        )
        .where(
            PriceAlert.product_id == product_id,
            PriceAlert.status == 0, # Đang Active
        )
    )
    result_alert = await db.execute(stmt_alert)
    candidate_alerts = result_alert.scalars().all()
    result = await _trigger_alert_rows(db, candidate_alerts)
    await _dispatch_triggered_notifications(db, result["notifications"], bg_tasks)
    return float(current_lowest_price)

async def remove_price_alert(db: AsyncSession, user_id: UUID, platform_product_id: UUID) -> None:
    """
    Xóa cảnh báo giá của một sản phẩm do người dùng đặt.
    """
    stmt = delete(PriceAlert).where(
        PriceAlert.user_id == user_id,
        PriceAlert.platform_product_id == platform_product_id,
    )
    result = await db.execute(stmt)
    await db.commit()

    # Nếu rowcount == 0 nghĩa là không tìm thấy cảnh báo nào để xóa
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy cảnh báo giá cho sản phẩm này.",
        )
