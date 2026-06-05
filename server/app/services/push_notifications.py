import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user_device_token import UserDeviceToken

logger = logging.getLogger(__name__)

INVALID_FCM_ERROR_CODES = {
    "UNREGISTERED",
    "INVALID_ARGUMENT",
    "registration-token-not-registered",
    "invalid-registration-token",
}

_firebase_initialized = False


def initialize_firebase_app() -> bool:
    global _firebase_initialized
    if _firebase_initialized:
        return True
    if not settings.FCM_ENABLED:
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.exception("FCM_ENABLED is true but firebase-admin is not installed")
        return False

    if firebase_admin._apps:
        _firebase_initialized = True
        return True

    if settings.FCM_SERVICE_ACCOUNT_FILE:
        cred = credentials.Certificate(settings.FCM_SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

    _firebase_initialized = True
    logger.info("Firebase Admin SDK initialized")
    return True


def _decimal_payload(value: Decimal | float | int | None) -> str:
    return "" if value is None else str(value)


def _is_invalid_token_error(exc: Exception | None) -> bool:
    if exc is None:
        return False
    code = getattr(exc, "code", None)
    if code in INVALID_FCM_ERROR_CODES:
        return True
    message = str(exc)
    return any(error_code in message for error_code in INVALID_FCM_ERROR_CODES)


async def send_price_alert_push(
    db: AsyncSession,
    user_id: UUID,
    product_id: UUID,
    platform_product_id: UUID,
    product_name: str,
    target_price: Decimal,
    current_price: Decimal,
) -> dict[str, int]:
    result = await db.execute(
        select(UserDeviceToken).where(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.is_active.is_(True),
        )
    )
    rows = result.scalars().all()
    tokens = [row.token for row in rows]
    if not tokens:
        return {"fcm_sent": 0, "invalid_tokens": 0}
    if not initialize_firebase_app():
        return {"fcm_sent": 0, "invalid_tokens": 0}

    from firebase_admin import messaging

    sent = 0
    invalid_tokens: list[str] = []
    data = {
        "type": "price_alert",
        "product_id": str(product_id),
        "platform_product_id": str(platform_product_id),
        "target_price": _decimal_payload(target_price),
        "current_price": _decimal_payload(current_price),
    }

    for start in range(0, len(tokens), 500):
        batch = tokens[start:start + 500]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="Price alert reached",
                body=f"{product_name} is now at or below your target price.",
            ),
            data=data,
            tokens=batch,
        )
        response = messaging.send_each_for_multicast(message)
        sent += response.success_count
        for index, item in enumerate(response.responses):
            if item.success:
                continue
            if _is_invalid_token_error(item.exception):
                invalid_tokens.append(batch[index])

    if invalid_tokens:
        invalid_set = set(invalid_tokens)
        for row in rows:
            if row.token in invalid_set:
                row.is_active = False
        await db.commit()

    return {"fcm_sent": sent, "invalid_tokens": len(invalid_tokens)}
