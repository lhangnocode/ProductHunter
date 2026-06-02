"""
Test suite cho Products API: /api/v1/products/
Bao gồm: search, get all, compare.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
import uuid

from app.api.v1 import products as products_api


# ============================================================
# SEARCH — /api/v1/products/search
# ============================================================
@pytest.mark.asyncio
async def test_search_products_missing_query(ac: AsyncClient):
    """Thiếu query param q → 422."""
    response = await ac.get("/api/v1/products/search")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_products_short_query(ac: AsyncClient):
    """Query quá ngắn (< 2 ký tự) → 422."""
    response = await ac.get("/api/v1/products/search?q=a")
    assert response.status_code == 422
    assert "String should have at least 2 characters" in str(response.json()["detail"])


@pytest.mark.asyncio
@patch('app.api.v1.products.search_product')
async def test_search_products_success(mock_search, ac: AsyncClient):
    """Tìm kiếm thành công → 200 + paginated response."""
    from app.models.product import Product
    import uuid
    mock_product = Product()
    mock_product.id = uuid.uuid4()
    mock_product.slug = "test-product"
    mock_product.normalized_name = "Test Product"
    mock_product.main_image_url = "http://example.com/img.jpg"

    mock_search.return_value = ([mock_product], 1)

    response = await ac.get("/api/v1/products/search?q=iphone")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["normalized_name"] == "Test Product"


@pytest.mark.asyncio
@patch('app.api.v1.products.search_product')
async def test_search_products_empty_result(mock_search, ac: AsyncClient):
    """Tìm kiếm không có kết quả → 200 + data rỗng."""
    mock_search.return_value = ([], 0)

    response = await ac.get("/api/v1/products/search?q=xyznotexist")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_results"] == 0
    assert data["total_pages"] == 0


@pytest.mark.asyncio
@patch('app.api.v1.products.search_product')
async def test_search_products_pagination(mock_search, ac: AsyncClient):
    """Kiểm tra pagination: page, limit → đúng current_page, total_pages."""
    from app.models.product import Product
    import uuid

    products = []
    for i in range(5):
        p = Product()
        p.id = uuid.uuid4()
        p.slug = f"product-{i}"
        p.normalized_name = f"Product {i}"
        p.main_image_url = None
        products.append(p)

    mock_search.return_value = (products, 25)

    response = await ac.get("/api/v1/products/search?q=product&page=2&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["current_page"] == 2
    assert data["total_pages"] == 5  # 25 / 5
    assert data["total_results"] == 25
    assert len(data["data"]) == 5


# ============================================================
# GET ALL — /api/v1/products/
# ============================================================
@pytest.mark.asyncio
async def test_get_all_products_empty(ac: AsyncClient):
    """Danh sách rỗng khi chưa có product nào."""
    response = await ac.get("/api/v1/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_products_with_data(ac: AsyncClient, created_product: dict):
    """Có data → trả về danh sách chứa product."""
    response = await ac.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = [p["normalized_name"] for p in data]
    assert "iPhone 15 Pro Max" in names


@pytest.mark.asyncio
async def test_get_all_products_with_skip_limit(ac: AsyncClient, created_product: dict):
    """Kiểm tra skip/limit params."""
    response = await ac.get("/api/v1/products/?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


# ============================================================
# COMPARE — /api/v1/products/compare
# ============================================================
@pytest.mark.asyncio
async def test_compare_missing_query(ac: AsyncClient):
    """Thiếu query param q → 422."""
    response = await ac.get("/api/v1/products/compare")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_compare_short_query(ac: AsyncClient):
    """Query quá ngắn → 422."""
    response = await ac.get("/api/v1/products/compare?q=a")
    assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.api.v1.products.search_product')
async def test_compare_success(mock_search, ac: AsyncClient):
    """So sánh giá thành công → 200."""
    from app.models.product import Product
    import uuid

    p = Product()
    p.id = uuid.uuid4()
    p.slug = "test-compare"
    p.normalized_name = "Test Compare"
    p.main_image_url = None
    p.platform_products = []

    mock_search.return_value = ([p], 1)

    response = await ac.get("/api/v1/products/compare?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "keyword" in data
    assert data["keyword"] == "test"
    assert "data" in data
    assert isinstance(data["data"], list)


def _fake_platform_product(price, in_stock=True, platform_id=1):
    return SimpleNamespace(
        platform_id=platform_id,
        url=f"https://example.com/{platform_id}",
        affiliate_url=None,
        current_price=price,
        original_price=price + 1000 if price is not None else None,
        in_stock=in_stock,
        last_crawled_at=None,
    )


def _fake_product(name, platform_products):
    return SimpleNamespace(
        id=uuid.uuid4(),
        normalized_name=name,
        product_name=name.title(),
        slug=name.replace(" ", "-"),
        main_image_url=None,
        platform_products=platform_products,
    )


@pytest.mark.asyncio
@patch("app.api.v1.products.search_product")
async def test_search_all_returns_platform_items_for_products_with_platforms(
    mock_search,
):
    product = _fake_product("phone", [_fake_platform_product(100), _fake_platform_product(90)])
    mock_search.return_value = ([product], 1)

    response = await products_api.search_products_list(q="phone", page=1, limit=20, db=AsyncMock())

    assert response["keyword"] == "phone"
    assert response["total_pages"] == 1
    assert len(response["data"]) == 2


@pytest.mark.asyncio
@patch("app.api.v1.products.search_product")
async def test_search_all_ignores_products_without_platforms(mock_search):
    product = _fake_product("phone", [])
    mock_search.return_value = ([product], 1)

    response = await products_api.search_products_list(q="phone", page=1, limit=20, db=AsyncMock())

    assert response["data"] == []


@pytest.mark.asyncio
@patch("app.api.v1.products.search_product")
async def test_compare_uses_in_stock_prices_and_ignores_out_of_stock(mock_search, ac: AsyncClient):
    product = _fake_product(
        "phone",
        [
            _fake_platform_product(500, in_stock=False, platform_id=1),
            _fake_platform_product(300, in_stock=True, platform_id=2),
        ],
    )
    mock_search.return_value = ([product], 1)

    response = await ac.get("/api/v1/products/compare?q=phone")

    assert response.status_code == 200
    item = response.json()["data"][0]
    assert item["lowest_price"] == 300
    assert len(item["platforms"]) == 2


@pytest.mark.asyncio
@patch("app.api.v1.products.search_product")
async def test_compare_no_valid_prices_returns_null_lowest_price(mock_search, ac: AsyncClient):
    product = _fake_product(
        "phone",
        [
            _fake_platform_product(None, in_stock=True),
            _fake_platform_product(500, in_stock=False),
        ],
    )
    mock_search.return_value = ([product], 1)

    response = await ac.get("/api/v1/products/compare?q=phone")

    assert response.status_code == 200
    assert response.json()["data"][0]["lowest_price"] is None


@pytest.mark.asyncio
@patch("app.api.v1.products.search_product")
async def test_compare_sorts_by_lowest_price(mock_search, ac: AsyncClient):
    expensive = _fake_product("expensive", [_fake_platform_product(900)])
    cheap = _fake_product("cheap", [_fake_platform_product(100)])
    no_price = _fake_product("no price", [])
    mock_search.return_value = ([expensive, no_price, cheap], 3)

    response = await ac.get("/api/v1/products/compare?q=phone")

    assert response.status_code == 200
    names = [item["normalized_name"] for item in response.json()["data"]]
    assert names == ["cheap", "expensive", "no price"]


@pytest.mark.asyncio
async def test_compare2_mock_data_branch(monkeypatch: pytest.MonkeyPatch, ac: AsyncClient, created_product: dict):
    monkeypatch.setattr(
        products_api,
        "MOCK_PLATFORM_DATA",
        [
            {
                "product_id": created_product["id"],
                "platform_id": 1,
                "url": "https://example.com/a",
                "affiliate_url": None,
                "current_price": 200,
                "original_price": 300,
                "in_stock": True,
                "last_crawled_at": None,
            },
            {
                "product_id": created_product["id"],
                "platform_id": 2,
                "url": "https://example.com/b",
                "affiliate_url": None,
                "current_price": 100,
                "original_price": 300,
                "in_stock": True,
                "last_crawled_at": None,
            },
        ],
    )

    response = await ac.get("/api/v1/products/compare2?q=iphone")

    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert data["data"][0]["lowest_price"] == 100


@pytest.mark.asyncio
async def test_compare2_skips_db_products_without_mock_platforms(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
    created_product: dict,
):
    monkeypatch.setattr(products_api, "MOCK_PLATFORM_DATA", [])

    response = await ac.get("/api/v1/products/compare2?q=iphone")

    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 0
    assert data["data"] == []
