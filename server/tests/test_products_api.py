"""
Test suite cho Products API: /api/v1/products/
Bao gồm: search, get all, compare.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


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
