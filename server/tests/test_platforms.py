"""
Test suite cho Platforms API: /api/v1/platforms/
Bao gồm: tạo platform, lấy danh sách, kiểm tra cleanup.
"""
import pytest
from httpx import AsyncClient


# ============================================================
# CREATE PLATFORM
# ============================================================
@pytest.mark.asyncio
async def test_create_platform(ac: AsyncClient):
    """Tạo platform mới → 201."""
    response = await ac.post("/api/v1/platforms/", json={
        "name": "Shopee",
        "base_url": "https://shopee.vn",
        "affiliate_config": None,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Shopee"
    assert data["base_url"] == "https://shopee.vn"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_platform_with_affiliate(ac: AsyncClient):
    """Tạo platform kèm affiliate config."""
    response = await ac.post("/api/v1/platforms/", json={
        "name": "Lazada",
        "base_url": "https://lazada.vn",
        "affiliate_config": '{"aff_id": "12345"}',
    })
    assert response.status_code == 201
    data = response.json()
    assert data["affiliate_config"] == '{"aff_id": "12345"}'


@pytest.mark.asyncio
async def test_create_platform_missing_name(ac: AsyncClient):
    """Thiếu tên platform → 422."""
    response = await ac.post("/api/v1/platforms/", json={
        "base_url": "https://shopee.vn",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_platform_missing_base_url(ac: AsyncClient):
    """Thiếu base_url → 422."""
    response = await ac.post("/api/v1/platforms/", json={
        "name": "Shopee",
    })
    assert response.status_code == 422


# ============================================================
# GET PLATFORMS
# ============================================================
@pytest.mark.asyncio
async def test_get_platforms_empty(ac: AsyncClient):
    """Danh sách rỗng khi chưa có platform nào."""
    response = await ac.get("/api/v1/platforms/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_platforms_after_create(ac: AsyncClient):
    """Tạo 2 platform rồi get → đúng 2 items."""
    await ac.post("/api/v1/platforms/", json={
        "name": "Shopee",
        "base_url": "https://shopee.vn",
    })
    await ac.post("/api/v1/platforms/", json={
        "name": "Tiki",
        "base_url": "https://tiki.vn",
    })

    response = await ac.get("/api/v1/platforms/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Shopee", "Tiki"}


# ============================================================
# VERIFY CLEANUP
# ============================================================
@pytest.mark.asyncio
async def test_cleanup_works(ac: AsyncClient):
    """
    Chứng minh data đã bị xóa sau test trước.
    Nếu cleanup đúng → danh sách platforms phải rỗng.
    """
    response = await ac.get("/api/v1/platforms/")
    assert response.status_code == 200
    assert response.json() == [], "Cleanup không hoạt động — vẫn còn data từ test trước!"
