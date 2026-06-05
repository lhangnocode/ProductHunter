import asyncio
import logging

from app.core.config import settings
from app.db.session import get_sessionmaker
from app.services.price_alert import check_and_trigger_system_alerts
from app.services.push_notifications import initialize_firebase_app

logger = logging.getLogger(__name__)


async def run_once() -> dict[str, int]:
    async with get_sessionmaker()() as db:
        result = await check_and_trigger_system_alerts(db)
    logger.info(
        "price_alert_worker checked=%s triggered=%s email_queued=%s fcm_sent=%s invalid_tokens=%s skipped_without_price=%s",
        result["checked_products"],
        result["triggered_alerts"],
        result["email_queued"],
        result["fcm_sent"],
        result["invalid_tokens"],
        result["skipped_without_price"],
    )
    return result


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if settings.FCM_ENABLED:
        initialize_firebase_app()

    interval = max(settings.PRICE_ALERT_CHECK_INTERVAL_SECONDS, 1)
    logger.info("price_alert_worker started interval_seconds=%s", interval)
    while True:
        try:
            await run_once()
        except Exception:
            logger.exception("price_alert_worker cycle failed")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
