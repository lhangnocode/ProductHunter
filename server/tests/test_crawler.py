"""
Test suite cho Crawler API: /api/v1/crawler/
Bao gồm: upload product, upload platform products.
API yêu cầu DEV_API_KEY header.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.core.config import settings


# ============================================================
# HELPER: Header API key hợp lệ
# ============================================================
def dev_api_headers() -> dict:
    return {"X-API-Key": settings.DEV_API_KEY}


# ============================================================
# AUTH — Kiểm tra require_dev_api_key
# ============================================================
@pytest.mark.asyncio
async def test_crawler_no_api_key(ac: AsyncClient):
    """Không gửi API key → 401."""
    response = await ac.post("/api/v1/crawler/products", json={
        "normalized_name": "Test",
        "slug": "test",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_crawler_wrong_api_key(ac: AsyncClient):
    """Sai API key → 401."""
    response = await ac.post(
        "/api/v1/crawler/products",
        json={"normalized_name": "Test", "slug": "test"},
        headers={"X-API-Key": "wrong-key-12345"},
    )
    assert response.status_code == 401


# ============================================================
# UPLOAD PRODUCT — POST /api/v1/crawler/products
# ============================================================
@pytest.mark.asyncio
@patch('app.api.v1.crawler.upsert_product')
async def test_upload_product_success(mock_upsert, ac: AsyncClient):
    """Upload product thành công → 200."""
    import uuid
    from app.models.product import Product

    mock_product = Product()
    mock_product.id = uuid.uuid4()
    mock_product.normalized_name = "iPhone 16"
    mock_product.slug = "iphone-16"
    mock_product.brand = "Apple"
    mock_product.category = "Điện thoại"
    mock_product.main_image_url = "https://example.com/img.jpg"
    mock_product.product_name = "iPhone 16 128GB"
    mock_product.created_at = "2026-01-01T00:00:00"

    mock_upsert.return_value = mock_product

    response = await ac.post(
        "/api/v1/crawler/products",
        json={
            "normalized_name": "iPhone 16",
            "slug": "iphone-16",
            "brand": "Apple",
            "category": "Điện thoại",
            "main_image_url": "https://example.com/img.jpg",
        },
        headers=dev_api_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["normalized_name"] == "iPhone 16"
    assert data["slug"] == "iphone-16"


@pytest.mark.asyncio
async def test_upload_product_missing_fields(ac: AsyncClient):
    """Thiếu trường bắt buộc → 422."""
    response = await ac.post(
        "/api/v1/crawler/products",
        json={"brand": "Apple"},
        headers=dev_api_headers(),
    )
    assert response.status_code == 422


# ============================================================
# UPLOAD PLATFORM PRODUCTS BULK — POST /api/v1/crawler/platform-products
# ============================================================
@pytest.mark.asyncio
async def test_upload_platform_products_no_api_key(ac: AsyncClient):
    """Không gửi API key cho bulk upload → 401."""
    response = await ac.post("/api/v1/crawler/platform-products", json=[])
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_platform_products_empty_list(ac: AsyncClient, created_platform: dict):
    """Gửi danh sách rỗng → 200 + list rỗng."""
    response = await ac.post(
        "/api/v1/crawler/platform-products",
        json=[],
        headers=dev_api_headers(),
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_upload_platform_products_success(
    ac: AsyncClient, created_platform: dict, created_product: dict
):
    """Upload bulk platform products thành công → 200 + list kết quả."""
    platform_id = created_platform["id"]
    product_id = created_product["id"]

    payload = [
        {
            "product_id": product_id,
            "platform_id": platform_id,
            "original_item_id": "crawl_item_001",
            "url": "https://shopee.vn/product-001",
            "current_price": 5000000,
            "original_price": 6000000,
            "in_stock": True,
        }
    ]

    response = await ac.post(
        "/api/v1/crawler/platform-products",
        json=payload,
        headers=dev_api_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["original_item_id"] == "crawl_item_001"
    assert data[0]["platform_id"] == platform_id


@pytest.mark.asyncio
async def test_upload_platform_products_missing_required(ac: AsyncClient):
    """Thiếu trường bắt buộc trong item → 422."""
    payload = [
        {
            "platform_id": 1,
            # thiếu original_item_id, url
        }
    ]
    response = await ac.post(
        "/api/v1/crawler/platform-products",
        json=payload,
        headers=dev_api_headers(),
    )
    assert response.status_code == 422
