from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import platform as _platform_model  # noqa: F401
from app.models import platform_product as _platform_product_model  # noqa: F401
from app.models import price_alert as _price_alert_model  # noqa: F401
from app.models import price_record as _price_record_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401
from app.services import wish_list as wish_list_service


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ExecuteResult:
    def __init__(self, *, scalar=None, rows=None, rowcount=1):
        self._scalar = scalar
        self._rows = rows or []
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return _Scalars(self._rows)


class _FakeSession:
    def __init__(self, *results):
        self._results = list(results)
        self.executed = []
        self.commits = 0

    async def execute(self, stmt):
        self.executed.append(stmt)
        if not self._results:
            raise AssertionError("No fake execute result configured")
        return self._results.pop(0)

    async def commit(self):
        self.commits += 1


def _wishlist_row(product=None):
    return SimpleNamespace(
        product_id=uuid4(),
        added_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
        product=product,
    )


@pytest.mark.asyncio
async def test_get_wishlist_rows_returns_loaded_rows():
    rows = [_wishlist_row(), _wishlist_row()]
    db = _FakeSession(_ExecuteResult(rows=rows))

    result = await wish_list_service._get_wishlist_rows(db, uuid4())

    assert result == rows


def test_to_response_maps_product_fields_when_product_exists():
    product = SimpleNamespace(
        normalized_name="iPhone 15 Pro Max",
        main_image_url="https://example.com/iphone.jpg",
    )
    row = _wishlist_row(product=product)

    response = wish_list_service._to_response([row])

    assert len(response.items) == 1
    assert response.items[0].product_id == row.product_id
    assert response.items[0].product_name == "iPhone 15 Pro Max"
    assert response.items[0].main_image_url == "https://example.com/iphone.jpg"


def test_to_response_handles_missing_product_relation():
    row = _wishlist_row(product=None)

    response = wish_list_service._to_response([row])

    assert response.items[0].product_name is None
    assert response.items[0].main_image_url is None


@pytest.mark.asyncio
async def test_add_to_wishlist_raises_404_when_product_missing():
    db = _FakeSession(_ExecuteResult(scalar=None))

    with pytest.raises(HTTPException) as exc:
        await wish_list_service.add_to_wishlist(db, uuid4(), uuid4())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Product not found"
    assert db.commits == 0


@pytest.mark.asyncio
async def test_add_to_wishlist_inserts_and_returns_current_wishlist():
    product_id = uuid4()
    row = _wishlist_row(
        product=SimpleNamespace(
            normalized_name="Galaxy S24",
            main_image_url="https://example.com/galaxy.jpg",
        )
    )
    row.product_id = product_id
    db = _FakeSession(
        _ExecuteResult(scalar=product_id),
        _ExecuteResult(),
        _ExecuteResult(rows=[row]),
    )

    response = await wish_list_service.add_to_wishlist(db, uuid4(), product_id)

    assert db.commits == 1
    assert len(db.executed) == 3
    assert response.items[0].product_id == product_id
    assert response.items[0].product_name == "Galaxy S24"


@pytest.mark.asyncio
async def test_get_user_wishlist_returns_response():
    row = _wishlist_row(product=SimpleNamespace(normalized_name="MacBook", main_image_url=None))
    db = _FakeSession(_ExecuteResult(rows=[row]))

    response = await wish_list_service.get_user_wishlist(db, uuid4())

    assert response.items[0].product_name == "MacBook"


@pytest.mark.asyncio
async def test_remove_from_wishlist_commits_when_row_deleted():
    db = _FakeSession(_ExecuteResult(rowcount=1))

    await wish_list_service.remove_from_wishlist(db, uuid4(), uuid4())

    assert db.commits == 1


@pytest.mark.asyncio
async def test_remove_from_wishlist_raises_404_when_row_missing():
    db = _FakeSession(_ExecuteResult(rowcount=0))

    with pytest.raises(HTTPException) as exc:
        await wish_list_service.remove_from_wishlist(db, uuid4(), uuid4())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Wishlist item not found"
    assert db.commits == 1
