import pytest

from app.handlers import handler_product as hp
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_search_product_blank_query_returns_empty():
    async with TestingSessionLocal() as db:
        assert await hp.search_product("", db) == ([], 0)
        assert await hp.search_product("   ", db) == ([], 0)


@pytest.mark.asyncio
async def test_search_product_typesense_success(monkeypatch, created_product):
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)
    monkeypatch.setattr(
        hp,
        "_typesense_search",
        lambda client, params: {
            "found": 1,
            "hits": [{"document": {"normalized_name": created_product["normalized_name"]}}],
        },
    )

    async with TestingSessionLocal() as db:
        products, total = await hp.search_product(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert total == 1
    assert [str(product.id) for product in products] == [created_product["id"]]


@pytest.mark.asyncio
async def test_search_product_typesense_skips_invalid_documents(monkeypatch):
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)
    monkeypatch.setattr(
        hp,
        "_typesense_search",
        lambda client, params: {
            "found": 3,
            "hits": [
                {"document": {"normalized_name": ""}},
                {"document": {}},
                {"document": {"normalized_name": None}},
            ],
        },
    )

    async with TestingSessionLocal() as db:
        products, total = await hp.search_product(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert total == 0
    assert products == []


@pytest.mark.asyncio
async def test_search_product_typesense_failure_falls_back_to_postgres(
    monkeypatch,
    created_product,
):
    monkeypatch.setattr(hp, "_ensure_typesense_collection", lambda client: None)

    def _raise_search(client, params):
        raise RuntimeError("typesense unavailable")

    monkeypatch.setattr(hp, "_typesense_search", _raise_search)

    async with TestingSessionLocal() as db:
        products, total = await hp.search_product(
            "iphone",
            db=db,
            typesense_client=object(),
        )

    assert total == 1
    assert [str(product.id) for product in products] == [created_product["id"]]


@pytest.mark.asyncio
async def test_search_product_postgres_no_results():
    async with TestingSessionLocal() as db:
        products, total = await hp.search_product("definitely-missing", db=db)

    assert products == []
    assert total == 0
