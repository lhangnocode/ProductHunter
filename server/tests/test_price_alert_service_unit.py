import uuid
from decimal import Decimal

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select

from app.models.platform_product import PlatformProduct
from app.models.price_alert import PriceAlert
from app.models.user import User
from app.services import price_alert as service
from tests.conftest import TestingSessionLocal


async def _get_user(email: str = "testuser@example.com") -> User:
    async with TestingSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one()


async def _add_alert(user_id, product_id, target_price, status=0) -> None:
    async with TestingSessionLocal() as db:
        db.add(
            PriceAlert(
                user_id=user_id,
                product_id=product_id,
                target_price=Decimal(target_price),
                status=status,
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_get_current_lowest_price_uses_in_stock_price(created_product, created_platform_product):
    async with TestingSessionLocal() as db:
        price = await service._get_current_lowest_price(db, uuid.UUID(created_product["id"]))

    assert float(price) == 28_990_000.0


@pytest.mark.asyncio
async def test_get_current_lowest_price_ignores_out_of_stock(created_product, created_platform_product):
    async with TestingSessionLocal() as db:
        result = await db.execute(
            select(PlatformProduct).where(PlatformProduct.id == uuid.UUID(created_platform_product["id"]))
        )
        platform_product = result.scalar_one()
        platform_product.in_stock = False
        await db.commit()

        price = await service._get_current_lowest_price(db, uuid.UUID(created_product["id"]))

    assert price is None


@pytest.mark.asyncio
async def test_get_current_lowest_price_ignores_null_price(created_product, created_platform_product):
    async with TestingSessionLocal() as db:
        result = await db.execute(
            select(PlatformProduct).where(PlatformProduct.id == uuid.UUID(created_platform_product["id"]))
        )
        platform_product = result.scalar_one()
        platform_product.current_price = None
        await db.commit()

        price = await service._get_current_lowest_price(db, uuid.UUID(created_product["id"]))

    assert price is None


@pytest.mark.asyncio
async def test_check_user_alerts_skips_when_no_current_price(auth_headers, created_product):
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 1_000_000)

    async with TestingSessionLocal() as db:
        result = await service.check_and_trigger_user_alerts(
            db=db,
            user_id=user.id,
            bg_tasks=BackgroundTasks(),
        )

    assert result == {
        "checked_products": 0,
        "triggered_alerts": 0,
        "skipped_without_price": 1,
    }


@pytest.mark.asyncio
async def test_check_user_alerts_triggers_when_target_meets_current_price(
    monkeypatch,
    auth_headers,
    created_product,
    created_platform_product,
):
    sent = []

    async def _fake_send(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(service, "send_price_drop_email_async", _fake_send)
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 30_000_000)
    bg_tasks = BackgroundTasks()

    async with TestingSessionLocal() as db:
        result = await service.check_and_trigger_user_alerts(
            db=db,
            user_id=user.id,
            bg_tasks=bg_tasks,
        )

    assert result["checked_products"] == 1
    assert result["triggered_alerts"] == 1
    assert len(bg_tasks.tasks) == 1


@pytest.mark.asyncio
async def test_check_user_alerts_does_not_trigger_below_current_price(
    auth_headers,
    created_product,
    created_platform_product,
):
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 10_000_000)
    bg_tasks = BackgroundTasks()

    async with TestingSessionLocal() as db:
        result = await service.check_and_trigger_user_alerts(
            db=db,
            user_id=user.id,
            bg_tasks=bg_tasks,
        )

    assert result["checked_products"] == 1
    assert result["triggered_alerts"] == 0
    assert bg_tasks.tasks == []


@pytest.mark.asyncio
async def test_check_user_alerts_filters_by_product_id(
    auth_headers,
    created_product,
    created_platform_product,
):
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 30_000_000)

    async with TestingSessionLocal() as db:
        result = await service.check_and_trigger_user_alerts(
            db=db,
            user_id=user.id,
            bg_tasks=BackgroundTasks(),
            product_id=uuid.uuid4(),
        )

    assert result["checked_products"] == 0
    assert result["triggered_alerts"] == 0


@pytest.mark.asyncio
async def test_check_user_alerts_missing_user_or_product_skips_email_but_updates_status(
    created_platform,
):
    orphan_user_id = uuid.uuid4()
    orphan_product_id = uuid.uuid4()

    async with TestingSessionLocal() as db:
        db.add(
            PlatformProduct(
                product_id=orphan_product_id,
                platform_id=created_platform["id"],
                raw_name="orphan product",
                original_item_id="orphan-1",
                url="https://example.com/orphan",
                current_price=Decimal(100),
                in_stock=True,
            )
        )
        db.add(
            PriceAlert(
                user_id=orphan_user_id,
                product_id=orphan_product_id,
                target_price=Decimal(100),
                status=0,
            )
        )
        await db.commit()

        bg_tasks = BackgroundTasks()
        result = await service.check_and_trigger_user_alerts(
            db=db,
            user_id=orphan_user_id,
            bg_tasks=bg_tasks,
        )
        alert = (
            await db.execute(select(PriceAlert).where(PriceAlert.user_id == orphan_user_id))
        ).scalar_one()

    assert result["triggered_alerts"] == 1
    assert alert.status == 1
    assert bg_tasks.tasks == []


@pytest.mark.asyncio
async def test_check_and_trigger_alerts_no_price_raises_404(created_product):
    async with TestingSessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            await service.check_and_trigger_alerts(
                db=db,
                product_id=uuid.UUID(created_product["id"]),
                bg_tasks=BackgroundTasks(),
            )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_check_and_trigger_alerts_no_matching_alerts_returns_current_price(
    auth_headers,
    created_product,
    created_platform_product,
):
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 1_000_000)

    async with TestingSessionLocal() as db:
        price = await service.check_and_trigger_alerts(
            db=db,
            product_id=product_id,
            bg_tasks=BackgroundTasks(),
        )

    assert price == 28_990_000.0


@pytest.mark.asyncio
async def test_check_and_trigger_alerts_matching_alerts_enqueue_email_and_mark_triggered(
    monkeypatch,
    auth_headers,
    created_product,
    created_platform_product,
):
    async def _fake_send(**kwargs):
        return None

    monkeypatch.setattr(service, "send_price_drop_email_async", _fake_send)
    user = await _get_user()
    product_id = uuid.UUID(created_product["id"])
    await _add_alert(user.id, product_id, 30_000_000)
    bg_tasks = BackgroundTasks()

    async with TestingSessionLocal() as db:
        price = await service.check_and_trigger_alerts(
            db=db,
            product_id=product_id,
            bg_tasks=bg_tasks,
        )
        alert = (
            await db.execute(
                select(PriceAlert).where(
                    PriceAlert.user_id == user.id,
                    PriceAlert.product_id == product_id,
                )
            )
        ).scalar_one()

    assert price == 28_990_000.0
    assert alert.status == 1
    assert len(bg_tasks.tasks) == 1
