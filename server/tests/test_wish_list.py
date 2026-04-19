"""
Test suite cho Wish List API: /api/v1/wish_lists/
Bao gồm: thêm, lấy danh sách, xóa.
Tất cả endpoint đều yêu cầu authentication.
"""
import pytest
from httpx import AsyncClient
import uuid


# ============================================================
# UNAUTHENTICATED → 401
# ============================================================
@pytest.mark.asyncio
async def test_add_wishlist_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.post("/api/v1/wish_lists/", json={
        "product_id": str(uuid.uuid4()),
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_wishlist_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.get("/api/v1/wish_lists/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_wishlist_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    fake_id = str(uuid.uuid4())
    response = await ac.delete(f"/api/v1/wish_lists/{fake_id}")
    assert response.status_code == 401


# ============================================================
# GET WISHLIST — GET /api/v1/wish_lists/
# ============================================================
@pytest.mark.asyncio
async def test_get_wishlist_empty(ac: AsyncClient, auth_headers: dict):
    """User chưa có wishlist item → 200 + items rỗng."""
    response = await ac.get("/api/v1/wish_lists/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["items"] == []


# ============================================================
# ADD TO WISHLIST — POST /api/v1/wish_lists/
# ============================================================
@pytest.mark.asyncio
async def test_add_to_wishlist_product_not_found(ac: AsyncClient, auth_headers: dict):
    """Thêm product không tồn tại → 404."""
    fake_id = str(uuid.uuid4())
    response = await ac.post("/api/v1/wish_lists/", json={
        "product_id": fake_id,
    }, headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_to_wishlist_success(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Thêm product vào wishlist thành công → 200."""
    product_id = created_product["id"]
    response = await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    product_ids = [item["product_id"] for item in data["items"]]
    assert product_id in product_ids


@pytest.mark.asyncio
async def test_add_to_wishlist_duplicate(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Thêm product trùng → vẫn 200 (on_conflict_do_nothing)."""
    product_id = created_product["id"]

    # Thêm lần 1
    await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)

    # Thêm lần 2 cùng product
    response = await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Không có duplicate
    matching = [item for item in data["items"] if item["product_id"] == product_id]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_add_to_wishlist_missing_product_id(ac: AsyncClient, auth_headers: dict):
    """Thiếu product_id → 422."""
    response = await ac.post("/api/v1/wish_lists/", json={}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_to_wishlist_invalid_uuid(ac: AsyncClient, auth_headers: dict):
    """UUID không hợp lệ → 422."""
    response = await ac.post("/api/v1/wish_lists/", json={
        "product_id": "not-a-uuid",
    }, headers=auth_headers)
    assert response.status_code == 422


# ============================================================
# GET WISHLIST AFTER ADD — verify data
# ============================================================
@pytest.mark.asyncio
async def test_get_wishlist_after_add(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Thêm rồi get → có data kèm product_name."""
    product_id = created_product["id"]

    # Add
    await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)

    # Get
    response = await ac.get("/api/v1/wish_lists/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1

    item = next(i for i in data["items"] if i["product_id"] == product_id)
    assert item["product_name"] == "iPhone 15 Pro Max"
    assert "added_at" in item


# ============================================================
# DELETE FROM WISHLIST — DELETE /api/v1/wish_lists/{product_id}
# ============================================================
@pytest.mark.asyncio
async def test_delete_wishlist_not_found(ac: AsyncClient, auth_headers: dict):
    """Xóa item không tồn tại → 404."""
    fake_id = str(uuid.uuid4())
    response = await ac.delete(f"/api/v1/wish_lists/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_wishlist_success(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Thêm rồi xóa → 200."""
    product_id = created_product["id"]

    # Add
    await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)

    # Delete
    response = await ac.delete(f"/api/v1/wish_lists/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "removed" in response.json()["message"].lower() or "wishlist" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_wishlist_then_get_empty(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Xóa xong → get lại phải không có item đó."""
    product_id = created_product["id"]

    # Add
    await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)

    # Delete
    await ac.delete(f"/api/v1/wish_lists/{product_id}", headers=auth_headers)

    # Verify
    response = await ac.get("/api/v1/wish_lists/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    product_ids = [item["product_id"] for item in data["items"]]
    assert product_id not in product_ids


@pytest.mark.asyncio
async def test_delete_wishlist_twice(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Xóa 2 lần → lần 2 phải 404."""
    product_id = created_product["id"]

    # Add
    await ac.post("/api/v1/wish_lists/", json={
        "product_id": product_id,
    }, headers=auth_headers)

    # Xóa lần 1
    resp1 = await ac.delete(f"/api/v1/wish_lists/{product_id}", headers=auth_headers)
    assert resp1.status_code == 200

    # Xóa lần 2
    resp2 = await ac.delete(f"/api/v1/wish_lists/{product_id}", headers=auth_headers)
    assert resp2.status_code == 404
