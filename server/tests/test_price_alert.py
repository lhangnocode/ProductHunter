"""
Test suite cho Price Alert API: /api/v1/price_alerts/
Bao gồm: tạo/cập nhật, lấy danh sách, xóa, trigger.
Tất cả endpoint đều yêu cầu authentication.
"""
import pytest
from httpx import AsyncClient
import uuid


# ============================================================
# UNAUTHENTICATED → 401
# ============================================================
@pytest.mark.asyncio
async def test_create_alert_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.post("/api/v1/price_alerts/", json={
        "product_id": str(uuid.uuid4()),
        "target_price": 5000000,
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_alerts_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.get("/api/v1/price_alerts/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_alert_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    fake_id = str(uuid.uuid4())
    response = await ac.delete(f"/api/v1/price_alerts/{fake_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_trigger_alert_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.post("/api/v1/price_alerts/trigger", json={
        "product_id": str(uuid.uuid4()),
        "current_lowest_price": 5000000,
    })
    assert response.status_code == 401


# ============================================================
# GET ALERTS — GET /api/v1/price_alerts/
# ============================================================
@pytest.mark.asyncio
async def test_get_alerts_empty(ac: AsyncClient, auth_headers: dict):
    """User chưa có alert → 200 + list rỗng."""
    response = await ac.get("/api/v1/price_alerts/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


# ============================================================
# CREATE ALERT — POST /api/v1/price_alerts/
# ============================================================
@pytest.mark.asyncio
async def test_create_alert_success(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Tạo alert thành công → 200."""
    product_id = created_product["id"]
    response = await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 25000000,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id
    assert data["target_price"] == 25000000
    assert data["status"] == 0  # ACTIVE


@pytest.mark.asyncio
async def test_create_alert_missing_product_id(ac: AsyncClient, auth_headers: dict):
    """Thiếu product_id → 422."""
    response = await ac.post("/api/v1/price_alerts/", json={
        "target_price": 5000000,
    }, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_missing_target_price(ac: AsyncClient, auth_headers: dict):
    """Thiếu target_price → 422."""
    response = await ac.post("/api/v1/price_alerts/", json={
        "product_id": str(uuid.uuid4()),
    }, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_alert_upsert(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Gửi lại alert cùng product → cập nhật target_price (UPSERT)."""
    product_id = created_product["id"]

    # Tạo lần 1
    await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 30000000,
    }, headers=auth_headers)

    # Tạo lần 2 cùng product → update
    response = await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 20000000,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["target_price"] == 20000000


# ============================================================
# GET ALERTS AFTER CREATE — verify data
# ============================================================
@pytest.mark.asyncio
async def test_get_alerts_after_create(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Tạo alert rồi get → có data."""
    product_id = created_product["id"]

    await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 22000000,
    }, headers=auth_headers)

    response = await ac.get("/api/v1/price_alerts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    product_ids = [alert["product_id"] for alert in data]
    assert product_id in product_ids


# ============================================================
# DELETE ALERT — DELETE /api/v1/price_alerts/{product_id}
# ============================================================
@pytest.mark.asyncio
async def test_delete_alert_not_found(ac: AsyncClient, auth_headers: dict):
    """Xóa alert không tồn tại → 404."""
    fake_id = str(uuid.uuid4())
    response = await ac.delete(f"/api/v1/price_alerts/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_alert_success(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Tạo rồi xóa alert → 200."""
    product_id = created_product["id"]

    # Tạo alert
    await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 18000000,
    }, headers=auth_headers)

    # Xóa
    response = await ac.delete(f"/api/v1/price_alerts/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "xóa" in response.json()["message"].lower() or "thành công" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_alert_twice(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Xóa alert 2 lần → lần 2 phải 404."""
    product_id = created_product["id"]

    # Tạo
    await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 15000000,
    }, headers=auth_headers)

    # Xóa lần 1
    resp1 = await ac.delete(f"/api/v1/price_alerts/{product_id}", headers=auth_headers)
    assert resp1.status_code == 200

    # Xóa lần 2
    resp2 = await ac.delete(f"/api/v1/price_alerts/{product_id}", headers=auth_headers)
    assert resp2.status_code == 404


# ============================================================
# TRIGGER — POST /api/v1/price_alerts/trigger
# ============================================================
@pytest.mark.asyncio
async def test_trigger_alert_success(
    ac: AsyncClient, auth_headers: dict, created_product: dict
):
    """Trigger price check → 200."""
    product_id = created_product["id"]

    # Tạo alert trước
    await ac.post("/api/v1/price_alerts/", json={
        "product_id": product_id,
        "target_price": 30000000,
    }, headers=auth_headers)

    # Trigger
    response = await ac.post("/api/v1/price_alerts/trigger", json={
        "product_id": product_id,
        "current_lowest_price": 25000000,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_trigger_alert_missing_fields(ac: AsyncClient, auth_headers: dict):
    """Thiếu trường bắt buộc → 422."""
    response = await ac.post("/api/v1/price_alerts/trigger", json={
        "product_id": str(uuid.uuid4()),
        # thiếu current_lowest_price
    }, headers=auth_headers)
    assert response.status_code == 422
