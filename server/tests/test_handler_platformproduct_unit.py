import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.handlers import handler_platformproduct as hp
from app.models.price_record import PriceRecord
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_search_platform_products_blank_query_returns_empty():
    async with TestingSessionLocal() as db:
        assert await hp.search_platform_products("", db) == []
        assert await hp.search_platform_products("   ", db) == []


@pytest.mark.asyncio
async def test_search_platform_products_typesense_success(monkeypatch, created_platform_product):
    product_id = created_platform_product["product_id"]
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)
    monkeypatch.setattr(
        hp,
        "_typesense_search",
        lambda client, params: {
            "hits": [{"document": {"id": product_id}}],
        },
    )

    async with TestingSessionLocal() as db:
        results = await hp.search_platform_products(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert [str(item.id) for item in results] == [created_platform_product["id"]]


@pytest.mark.asyncio
async def test_search_platform_products_typesense_skips_invalid_ids(monkeypatch):
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)
    monkeypatch.setattr(
        hp,
        "_typesense_search",
        lambda client, params: {
            "hits": [
                {"document": {"id": "not-a-uuid"}},
                {"document": {}},
                {"document": {"id": ""}},
            ],
        },
    )

    async with TestingSessionLocal() as db:
        results = await hp.search_platform_products(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert results == []


@pytest.mark.asyncio
async def test_search_platform_products_typesense_failure_falls_back_to_postgres(
    monkeypatch,
    created_platform_product,
):
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)

    def _raise_search(client, params):
        raise RuntimeError("typesense unavailable")

    monkeypatch.setattr(hp, "_typesense_search", _raise_search)

    async with TestingSessionLocal() as db:
        results = await hp.search_platform_products(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert [str(item.id) for item in results] == [created_platform_product["id"]]


@pytest.mark.asyncio
async def test_search_platform_products_postgres_no_matches_returns_empty():
    async with TestingSessionLocal() as db:
        results = await hp.search_platform_products("definitely-missing", db=db)

    assert results == []


@pytest.mark.asyncio
async def test_get_platform_products_by_product_id(created_platform_product):
    product_id = uuid.UUID(created_platform_product["product_id"])

    async with TestingSessionLocal() as db:
        results = await hp.get_platform_products_by_product_id(product_id, db=db)

    assert [str(item.id) for item in results] == [created_platform_product["id"]]


async def _add_price_records(platform_product_id: str, prices: list[int]) -> None:
    async with TestingSessionLocal() as db:
        for price in prices:
            db.add(
                PriceRecord(
                    platform_product_id=uuid.UUID(platform_product_id),
                    price=Decimal(price),
                    original_price=Decimal(price + 1000),
                )
            )
        await db.commit()


@pytest.mark.asyncio
async def test_get_trending_deals_extreme_deal_cleans_image(created_platform_product):
    await _add_price_records(
        created_platform_product["id"],
        [28_990_000, 35_000_000],
    )

    async with TestingSessionLocal() as db:
        deals = await hp.get_trending_deals(db=db, limit=10)

    assert len(deals) == 1
    assert deals[0].deal_status == "extreme"
    assert deals[0].deal_label == "Rẻ kỷ lục"
    assert deals[0].main_image_url == "https://example.com/iphone15.jpg"


@pytest.mark.asyncio
async def test_get_trending_deals_good_deal(created_platform_product):
    await _add_price_records(
        created_platform_product["id"],
        [20_000_000, 40_000_000],
    )

    async with TestingSessionLocal() as db:
        deals = await hp.get_trending_deals(db=db, limit=10)

    assert len(deals) == 1
    assert deals[0].deal_status == "good"
    assert deals[0].deal_label == "Giá tốt"


@pytest.mark.asyncio
async def test_get_trending_deals_no_qualifying_deal(created_platform_product):
    await _add_price_records(
        created_platform_product["id"],
        [10_000_000, 15_000_000],
    )

    async with TestingSessionLocal() as db:
        deals = await hp.get_trending_deals(db=db, limit=10)

    assert deals == []


@pytest.mark.asyncio
async def test_get_trending_deals_returns_empty_on_query_exception():
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("database unavailable")

    assert await hp.get_trending_deals(db=db, limit=10) == []
