from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import uuid

import pytest
from fastapi import HTTPException

from app.api.v1 import price_record as price_record_api
from app.schemas.price_record import PriceRecordCreateRequest


class FakeScalarResult:
    def __init__(self, values=None, one=None):
        self._values = values or []
        self._one = one

    def all(self):
        return self._values

    def scalar_one_or_none(self):
        return self._one


class FakeExecuteResult:
    def __init__(self, values=None, one=None):
        self._scalars = FakeScalarResult(values=values, one=one)

    def scalars(self):
        return self._scalars

    def scalar_one_or_none(self):
        return self._scalars.scalar_one_or_none()


@pytest.mark.asyncio
async def test_get_price_record_route_functions_return_scalars():
    records = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = FakeExecuteResult(values=records)

    all_records = await price_record_api.get_all_price_records(db=db, limit=10, offset=0)
    by_product = await price_record_api.get_price_record_by_platform_product_id(
        platform_product_id=uuid.uuid4(),
        db=db,
    )

    assert all_records == records
    assert by_product == records


@pytest.mark.asyncio
async def test_create_price_record_helper_adds_record():
    db = AsyncMock()
    db.add = MagicMock()
    platform_product = SimpleNamespace(id=uuid.uuid4())

    record = await price_record_api.create_price_record(
        db=db,
        platform_product=platform_product,
        payload_dict={
            "current_price": 100,
            "original_price": 150,
            "is_flash_sale": True,
        },
    )

    assert record.platform_product_id == platform_product.id
    assert record.price == 100
    assert record.is_flash_sale is True
    db.add.assert_called_once_with(record)


@pytest.mark.asyncio
async def test_push_price_record_direct_not_found_and_success():
    missing_db = AsyncMock()
    missing_db.add = MagicMock()
    missing_db.execute.return_value = FakeExecuteResult(one=None)
    payload = PriceRecordCreateRequest(platform_product_id=uuid.uuid4(), price=100)

    with pytest.raises(HTTPException) as exc_info:
        await price_record_api.push_price_record(payload=payload, db=missing_db)

    assert exc_info.value.status_code == 404

    found_db = AsyncMock()
    found_db.add = MagicMock()
    found_db.execute.return_value = FakeExecuteResult(one=SimpleNamespace(id=payload.platform_product_id))
    recorded_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    payload = PriceRecordCreateRequest(
        platform_product_id=payload.platform_product_id,
        price=100,
        original_price=150,
        is_flash_sale=True,
        recorded_at=recorded_at,
    )

    record = await price_record_api.push_price_record(payload=payload, db=found_db)

    assert record.price == 100
    assert record.original_price == 150
    assert record.is_flash_sale is True
    assert record.recorded_at == recorded_at
    found_db.add.assert_called_once_with(record)
    found_db.commit.assert_awaited_once()
    found_db.refresh.assert_awaited_once_with(record)


@pytest.mark.asyncio
async def test_push_price_records_batch_direct_mixed_and_empty():
    valid_id = uuid.uuid4()
    invalid_id = uuid.uuid4()
    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        FakeExecuteResult(one=SimpleNamespace(id=valid_id)),
        FakeExecuteResult(one=None),
    ]

    records = await price_record_api.push_price_records_batch(
        payload=[
            PriceRecordCreateRequest(platform_product_id=valid_id, price=100),
            PriceRecordCreateRequest(platform_product_id=invalid_id, price=200),
        ],
        db=db,
    )

    assert len(records) == 1
    assert records[0].platform_product_id == valid_id
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(records[0])

    empty_db = AsyncMock()
    empty_db.add = MagicMock()
    assert await price_record_api.push_price_records_batch(payload=[], db=empty_db) == []
    empty_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_price_analysis_delegates_to_handler(monkeypatch: pytest.MonkeyPatch):
    async def _fake_analyze(db, platform_product_id, current_price, original_price):
        return {
            "platform_product_id": str(platform_product_id),
            "current_price": current_price,
            "original_price": original_price,
        }

    monkeypatch.setattr(price_record_api, "analyze_price_status", _fake_analyze)
    platform_product_id = uuid.uuid4()

    result = await price_record_api.get_price_analysis(
        platform_product_id=platform_product_id,
        current_price=100,
        original_price=150,
        db=AsyncMock(),
    )

    assert result["platform_product_id"] == str(platform_product_id)
