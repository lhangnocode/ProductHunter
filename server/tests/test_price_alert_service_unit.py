import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select

from app.models import platform as _platform_model  # noqa: F401
from app.models import product as _product_model  # noqa: F401
from app.models import price_record as _price_record_model  # noqa: F401
from app.models import wish_list as _wish_list_model  # noqa: F401
from app.models.platform_product import PlatformProduct
from app.models.price_alert import PriceAlert
from app.models.user import User
from app.schemas.price_alert import PriceAlertCreate
from app.services import price_alert as service
from tests.conftest import TestingSessionLocal


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ExecuteResult:
    def __init__(self, *, scalar=None, row=None, rows=None, rowcount=1):
        self._scalar = scalar
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        return self._row

    def scalars(self):
        return _Scalars(self._rows)


class _FakeSession:
    def __init__(self, *results, scalar_result=None):
        self._results = list(results)
        self.scalar_result = scalar_result
        self.executed = []
        self.commits = 0

    async def execute(self, stmt):
        self.executed.append(stmt)
        if not self._results:
            raise AssertionError("No fake execute result configured")
        return self._results.pop(0)

    async def scalar(self, stmt):
        self.executed.append(stmt)
        return self.scalar_result

    async def commit(self):
        self.commits += 1


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


@pytest.mark.asyncio
async def test_set_price_alert_free_user_counts_new_alert_and_returns_product_data():
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    product = SimpleNamespace(
        normalized_name="iPhone 16",
        main_image_url="https://example.com/iphone16.jpg",
    )
    row = SimpleNamespace(
        product_id=product_id,
        target_price=Decimal("21000000"),
        status=0,
        product=product,
    )
    db = _FakeSession(
        _ExecuteResult(scalar=None),
        _ExecuteResult(),
        _ExecuteResult(row=row),
        scalar_result=4,
    )

    result = await service.set_price_alert(
        db=db,
        user_id=user_id,
        alert_in=PriceAlertCreate(product_id=product_id, target_price=Decimal("21000000")),
        user_plan=0,
    )

    assert db.commits == 1
    assert len(db.executed) == 4
    assert result == {
        "product_id": product_id,
        "target_price": Decimal("21000000"),
        "status": 0,
        "product_name": "iPhone 16",
        "main_image_url": "https://example.com/iphone16.jpg",
    }


@pytest.mark.asyncio
async def test_set_price_alert_free_user_at_limit_raises_403_before_insert():
    product_id = uuid.uuid4()
    db = _FakeSession(_ExecuteResult(scalar=None), scalar_result=service.FREE_PLAN_PRICE_ALERT_LIMIT)

    with pytest.raises(HTTPException) as exc:
        await service.set_price_alert(
            db=db,
            user_id=uuid.uuid4(),
            alert_in=PriceAlertCreate(product_id=product_id, target_price=Decimal("100")),
            user_plan=0,
        )

    assert exc.value.status_code == 403
    assert "up to 5 products" in exc.value.detail
    assert db.commits == 0
    assert len(db.executed) == 2


@pytest.mark.asyncio
async def test_set_price_alert_existing_alert_skips_free_limit_count_and_uses_fallback_product_data():
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    existing_alert_id = uuid.uuid4()
    row = SimpleNamespace(
        product_id=product_id,
        target_price=Decimal("100"),
        status=0,
        product=None,
    )
    db = _FakeSession(
        _ExecuteResult(scalar=existing_alert_id),
        _ExecuteResult(),
        _ExecuteResult(row=row),
    )

    result = await service.set_price_alert(
        db=db,
        user_id=user_id,
        alert_in=PriceAlertCreate(product_id=product_id, target_price=Decimal("100")),
        user_plan=0,
    )

    assert db.commits == 1
    assert len(db.executed) == 3
    assert result["product_name"] == "Sản phẩm"
    assert result["main_image_url"] is None


@pytest.mark.asyncio
async def test_set_price_alert_pro_user_skips_free_limit_count():
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    row = SimpleNamespace(
        product_id=product_id,
        target_price=Decimal("100"),
        status=0,
        product=SimpleNamespace(normalized_name="Pro Product", main_image_url=None),
    )
    db = _FakeSession(
        _ExecuteResult(scalar=None),
        _ExecuteResult(),
        _ExecuteResult(row=row),
    )

    result = await service.set_price_alert(
        db=db,
        user_id=user_id,
        alert_in=PriceAlertCreate(product_id=product_id, target_price=Decimal("100")),
        user_plan=1,
    )

    assert db.commits == 1
    assert len(db.executed) == 3
    assert result["product_name"] == "Pro Product"


@pytest.mark.asyncio
async def test_get_user_alerts_maps_rows_with_and_without_product_data():
    with_product = SimpleNamespace(
        product_id=uuid.uuid4(),
        target_price=Decimal("100"),
        status=0,
        product=SimpleNamespace(
            normalized_name="Known Product",
            main_image_url="https://example.com/known.jpg",
        ),
    )
    without_product = SimpleNamespace(
        product_id=uuid.uuid4(),
        target_price=Decimal("200"),
        status=1,
        product=None,
    )
    db = _FakeSession(_ExecuteResult(rows=[with_product, without_product]))

    result = await service.get_user_alerts(db, uuid.uuid4())

    assert result == [
        {
            "product_id": with_product.product_id,
            "target_price": Decimal("100"),
            "status": 0,
            "product_name": "Known Product",
            "main_image_url": "https://example.com/known.jpg",
        },
        {
            "product_id": without_product.product_id,
            "target_price": Decimal("200"),
            "status": 1,
            "product_name": "Sản phẩm không xác định",
            "main_image_url": None,
        },
    ]


@pytest.mark.asyncio
async def test_check_and_trigger_alerts_missing_user_or_product_skips_email_but_marks_status(monkeypatch):
    async def _fake_lowest_price(_db, _product_id):
        return Decimal("100")

    monkeypatch.setattr(service, "_get_current_lowest_price", _fake_lowest_price)
    alert = SimpleNamespace(user=None, product=None, status=0)
    db = _FakeSession(_ExecuteResult(rows=[alert]))
    bg_tasks = BackgroundTasks()

    price = await service.check_and_trigger_alerts(
        db=db,
        product_id=uuid.uuid4(),
        bg_tasks=bg_tasks,
    )

    assert price == 100.0
    assert alert.status == 1
    assert bg_tasks.tasks == []
    assert db.commits == 1


@pytest.mark.asyncio
async def test_remove_price_alert_raises_404_when_row_missing_direct_service():
    db = _FakeSession(_ExecuteResult(rowcount=0))

    with pytest.raises(HTTPException) as exc:
        await service.remove_price_alert(db, uuid.uuid4(), uuid.uuid4())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Không tìm thấy cảnh báo giá cho sản phẩm này."
    assert db.commits == 1
