import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_search_products_missing_query(ac: AsyncClient):
    response = await ac.get("/api/v1/products/search")
    assert response.status_code == 422 # FastAPI built-in validation error for missing query param

@pytest.mark.asyncio
async def test_search_products_short_query(ac: AsyncClient):
    response = await ac.get("/api/v1/products/search?q=a")
    assert response.status_code == 422
    assert "String should have at least 2 characters" in str(response.json()["detail"])

@pytest.mark.asyncio
@patch('app.api.v1.products.search_product')
async def test_search_products_success(mock_search, ac: AsyncClient):
    # Mocking handler search_product which returns (products, total_results)
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
