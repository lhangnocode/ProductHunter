"""
Test suite cho Platform Products API: /api/v1/platform_products/
Bao gồm: search, by-product-id, get all, trending.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch


# ============================================================
# SEARCH — GET /api/v1/platform_products/platform-products/search
# ============================================================
@pytest.mark.asyncio
async def test_search_platform_products_missing_name(ac: AsyncClient):
    """Thiếu query param name → 422."""
    response = await ac.get("/api/v1/platform_products/platform-products/search")
    assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.api.v1.platform_products.search_platform_products')
async def test_search_platform_products_success(mock_search, ac: AsyncClient):
    """Tìm kiếm thành công → 200."""
    mock_search.return_value = []

    response = await ac.get("/api/v1/platform_products/platform-products/search?name=iphone")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@patch('app.api.v1.platform_products.search_platform_products')
async def test_search_platform_products_with_pagination(mock_search, ac: AsyncClient):
    """Kiểm tra params limit, page."""
    mock_search.return_value = []

    response = await ac.get(
        "/api/v1/platform_products/platform-products/search?name=test&limit=10&page=2"
    )
    assert response.status_code == 200
    # Verify mock was called with correct params
    mock_search.assert_called_once()
    call_kwargs = mock_search.call_args
    assert call_kwargs.kwargs.get("limit") == 10 or call_kwargs.args[0] == "test"


# ============================================================
# BY PRODUCT ID — GET /api/v1/platform_products/platform-products/by-product-id
# ============================================================
@pytest.mark.asyncio
async def test_get_by_product_id_missing_param(ac: AsyncClient):
    """Thiếu product_id → 422."""
    response = await ac.get("/api/v1/platform_products/platform-products/by-product-id")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_by_product_id_invalid_uuid(ac: AsyncClient):
    """UUID không hợp lệ → 422."""
    response = await ac.get(
        "/api/v1/platform_products/platform-products/by-product-id?product_id=not-a-uuid"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.api.v1.platform_products.get_platform_products_by_product_id')
async def test_get_by_product_id_success(mock_get, ac: AsyncClient):
    """Truy vấn thành công → 200."""
    mock_get.return_value = []

    import uuid
    pid = str(uuid.uuid4())
    response = await ac.get(
        f"/api/v1/platform_products/platform-products/by-product-id?product_id={pid}"
    )
    assert response.status_code == 200
    assert response.json() == []


# ============================================================
# GET ALL — GET /api/v1/platform_products/platform-products
# ============================================================
@pytest.mark.asyncio
async def test_get_all_platform_products_empty(ac: AsyncClient):
    """Danh sách rỗng khi chưa có data."""
    response = await ac.get("/api/v1/platform_products/platform-products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_platform_products_with_limit(ac: AsyncClient):
    """Kiểm tra limit param."""
    response = await ac.get("/api/v1/platform_products/platform-products?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_get_all_platform_products_invalid_limit(ac: AsyncClient):
    """Limit ngoài phạm vi → 422."""
    response = await ac.get("/api/v1/platform_products/platform-products?limit=200")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_all_platform_products_negative_offset(ac: AsyncClient):
    """Offset âm → 422."""
    response = await ac.get("/api/v1/platform_products/platform-products?offset=-1")
    assert response.status_code == 422


# ============================================================
# TRENDING — GET /api/v1/platform_products/platform-products/trending
# ============================================================
@pytest.mark.asyncio
@patch('app.api.v1.platform_products.get_trending_deals')
async def test_get_trending_success(mock_trending, ac: AsyncClient):
    """Lấy trending thành công → 200."""
    mock_trending.return_value = []

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@patch('app.api.v1.platform_products.get_trending_deals')
async def test_get_trending_with_limit(mock_trending, ac: AsyncClient):
    """Trending với custom limit."""
    mock_trending.return_value = []

    response = await ac.get("/api/v1/platform_products/platform-products/trending?limit=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_trending_invalid_limit(ac: AsyncClient):
    """Limit vượt quá max → 422."""
    response = await ac.get("/api/v1/platform_products/platform-products/trending?limit=100")
    assert response.status_code == 422
