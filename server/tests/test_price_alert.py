"""
Test suite cho Price Alert API: /api/v1/price_alerts/
Bao gồm: tạo/cập nhật, lấy danh sách, xóa, trigger.
Tất cả endpoint đều yêu cầu authentication.
"""
import pytest
from httpx import AsyncClient
import uuid
from decimal import Decimal
from app.models.platform import Platform
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from tests.conftest import TestingSessionLocal


async def _create_alert_products(count: int) -> list[str]:
    platform_product_ids: list[str] = []
    async with TestingSessionLocal() as session:
        platform = Platform(name="Alert Test Platform", base_url="https://alerts.example.com")
        session.add(platform)
        await session.flush()
        for index in range(count):
            product_id = uuid.uuid4()
            product = Product(
                id=product_id,
                normalized_name=f"Alert Limit Product {product_id.hex[:8]}",
                product_name=f"Alert Limit Product {product_id.hex}",
                slug=f"alert-limit-product-{product_id.hex}",
                brand="Test",
                category="Test",
                main_image_url="https://example.com/alert-limit.jpg",
            )
            session.add(product)
            platform_product = PlatformProduct(
                id=uuid.uuid4(),
                product_id=product_id,
                platform_id=platform.id,
                raw_name=f"Alert Limit Offer {index}",
                original_item_id=f"alert-limit-offer-{product_id.hex}",
                url=f"https://alerts.example.com/{product_id.hex}",
                current_price=Decimal("999000"),
                in_stock=True,
            )
            session.add(platform_product)
            platform_product_ids.append(str(platform_product.id))
        await session.commit()
    return platform_product_ids


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
    ac: AsyncClient, auth_headers: dict, created_product: dict, created_platform_product: dict
):
    """Tạo alert thành công → 200."""
    product_id = created_product["id"]
    response = await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
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
    ac: AsyncClient, auth_headers: dict, created_product: dict, created_platform_product: dict
):
    """Gửi lại alert cùng product → cập nhật target_price (UPSERT)."""
    product_id = created_product["id"]

    # Tạo lần 1
    await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
        "target_price": 30000000,
    }, headers=auth_headers)

    # Tạo lần 2 cùng product → update
    response = await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
        "target_price": 20000000,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["target_price"] == 20000000


@pytest.mark.asyncio
async def test_free_user_can_create_five_price_alerts(ac: AsyncClient, auth_headers: dict):
    platform_product_ids = await _create_alert_products(5)

    for platform_product_id in platform_product_ids:
        response = await ac.post("/api/v1/price_alerts/", json={
            "platform_product_id": platform_product_id,
            "target_price": 1000000,
        }, headers=auth_headers)
        assert response.status_code == 200

    response = await ac.get("/api/v1/price_alerts/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5


@pytest.mark.asyncio
async def test_free_user_sixth_distinct_price_alert_is_forbidden(
    ac: AsyncClient,
    auth_headers: dict,
):
    platform_product_ids = await _create_alert_products(6)

    for platform_product_id in platform_product_ids[:5]:
        response = await ac.post("/api/v1/price_alerts/", json={
            "platform_product_id": platform_product_id,
            "target_price": 1000000,
        }, headers=auth_headers)
        assert response.status_code == 200

    response = await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": platform_product_ids[5],
        "target_price": 1000000,
    }, headers=auth_headers)

    assert response.status_code == 403
    assert "up to 5 products" in response.json()["detail"]


@pytest.mark.asyncio
async def test_free_user_can_update_existing_alert_at_limit(
    ac: AsyncClient,
    auth_headers: dict,
):
    platform_product_ids = await _create_alert_products(5)

    for platform_product_id in platform_product_ids:
        response = await ac.post("/api/v1/price_alerts/", json={
            "platform_product_id": platform_product_id,
            "target_price": 1000000,
        }, headers=auth_headers)
        assert response.status_code == 200

    response = await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": platform_product_ids[0],
        "target_price": 2000000,
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["target_price"] == 2000000


@pytest.mark.asyncio
async def test_premium_user_can_create_more_than_five_price_alerts(
    ac: AsyncClient,
    premium_auth_headers: dict,
):
    platform_product_ids = await _create_alert_products(6)

    for platform_product_id in platform_product_ids:
        response = await ac.post("/api/v1/price_alerts/", json={
            "platform_product_id": platform_product_id,
            "target_price": 1000000,
        }, headers=premium_auth_headers)
        assert response.status_code == 200

    response = await ac.get("/api/v1/price_alerts/", headers=premium_auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 6


@pytest.mark.asyncio
async def test_delete_price_alert_frees_free_user_slot(
    ac: AsyncClient,
    auth_headers: dict,
):
    platform_product_ids = await _create_alert_products(6)

    for platform_product_id in platform_product_ids[:5]:
        response = await ac.post("/api/v1/price_alerts/", json={
            "platform_product_id": platform_product_id,
            "target_price": 1000000,
        }, headers=auth_headers)
        assert response.status_code == 200

    delete_response = await ac.delete(f"/api/v1/price_alerts/{platform_product_ids[0]}", headers=auth_headers)
    assert delete_response.status_code == 200

    response = await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": platform_product_ids[5],
        "target_price": 1000000,
    }, headers=auth_headers)

    assert response.status_code == 200


# ============================================================
# GET ALERTS AFTER CREATE — verify data
# ============================================================
@pytest.mark.asyncio
async def test_get_alerts_after_create(
    ac: AsyncClient, auth_headers: dict, created_product: dict, created_platform_product: dict
):
    """Tạo alert rồi get → có data."""
    product_id = created_product["id"]

    await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
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
    ac: AsyncClient, auth_headers: dict, created_product: dict, created_platform_product: dict
):
    """Tạo rồi xóa alert → 200."""
    product_id = created_product["id"]

    # Tạo alert
    await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
        "target_price": 18000000,
    }, headers=auth_headers)

    # Xóa
    response = await ac.delete(f"/api/v1/price_alerts/{created_platform_product['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert "xóa" in response.json()["message"].lower() or "thành công" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_delete_alert_twice(
    ac: AsyncClient, auth_headers: dict, created_product: dict, created_platform_product: dict
):
    """Xóa alert 2 lần → lần 2 phải 404."""
    product_id = created_product["id"]

    # Tạo
    await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
        "target_price": 15000000,
    }, headers=auth_headers)

    # Xóa lần 1
    resp1 = await ac.delete(f"/api/v1/price_alerts/{created_platform_product['id']}", headers=auth_headers)
    assert resp1.status_code == 200

    # Xóa lần 2
    resp2 = await ac.delete(f"/api/v1/price_alerts/{created_platform_product['id']}", headers=auth_headers)
    assert resp2.status_code == 404


# ============================================================
# TRIGGER — POST /api/v1/price_alerts/trigger
# ============================================================
@pytest.mark.asyncio
async def test_trigger_alert_success(
    ac: AsyncClient,
    auth_headers: dict,
    created_product: dict,
    created_platform_product: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    """Trigger price check → 200."""
    product_id = created_product["id"]

    async def _fake_send_price_drop_email_async(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.services.price_alert.send_price_drop_email_async",
        _fake_send_price_drop_email_async,
    )

    # Tạo alert trước
    await ac.post("/api/v1/price_alerts/", json={
        "platform_product_id": created_platform_product["id"],
        "target_price": 30000000,
    }, headers=auth_headers)

    # Trigger toàn bộ danh sách alert của user hiện tại
    response = await ac.post("/api/v1/price_alerts/trigger", json={}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["checked_products"] == 1
    assert data["triggered_alerts"] == 1
    assert data["skipped_without_price"] == 0


@pytest.mark.asyncio
async def test_trigger_alert_empty_list(ac: AsyncClient, auth_headers: dict):
    """User chưa có alert → trigger thành công nhưng không kiểm tra sản phẩm nào."""
    response = await ac.post("/api/v1/price_alerts/trigger", json={}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["checked_products"] == 0
    assert data["triggered_alerts"] == 0
