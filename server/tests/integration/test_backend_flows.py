import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_password_reset_token


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class _FakeTypesenseDocuments:
    def upsert(self, document):
        return document


class _FakeTypesenseCollection:
    def __init__(self):
        self.documents = _FakeTypesenseDocuments()

    def retrieve(self):
        return {
            "fields": [
                {"name": "normalized_name", "type": "string", "infix": True},
                {"name": "product_name", "type": "string", "infix": True},
            ]
        }


class _FakeTypesenseCollections:
    def __init__(self):
        self._products = _FakeTypesenseCollection()

    def __getitem__(self, name):
        assert name == "products"
        return self._products

    def create(self, schema):
        return schema


class _FakeTypesenseClient:
    def __init__(self):
        self.collections = _FakeTypesenseCollections()


def _patch_password_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_hash(password: str) -> str:
        return f"test-hash:{password}"

    def _fake_verify(plain_password: str, hashed_password: str) -> bool:
        return hashed_password == _fake_hash(plain_password)

    monkeypatch.setattr("app.services.user.get_password_hash", _fake_hash)
    monkeypatch.setattr("app.api.v1.auth.get_password_hash", _fake_hash)
    monkeypatch.setattr("app.api.v1.auth.verify_password", _fake_verify)


async def _register_and_login(ac: AsyncClient, email: str, password: str) -> dict:
    register_resp = await ac.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Integration User",
        },
    )
    assert register_resp.status_code == 200

    login_resp = await ac.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_auth_lifecycle_register_login_refresh_reset(
    ac: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    _patch_password_hashing(monkeypatch)
    email = "integration-auth@example.com"
    old_password = "OldPass@1234"
    new_password = "NewPass@1234"

    headers = await _register_and_login(ac, email, old_password)

    me_resp = await ac.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    login_resp = await ac.post(
        "/api/v1/auth/login",
        data={"username": email, "password": old_password},
    )
    refresh_resp = await ac.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_resp.json()["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["token_type"] == "bearer"

    reset_resp = await ac.post(
        "/api/v1/auth/reset-password",
        json={
            "token": create_password_reset_token(email),
            "new_password": new_password,
        },
    )
    assert reset_resp.status_code == 200

    old_login_resp = await ac.post(
        "/api/v1/auth/login",
        data={"username": email, "password": old_password},
    )
    assert old_login_resp.status_code == 400

    new_login_resp = await ac.post(
        "/api/v1/auth/login",
        data={"username": email, "password": new_password},
    )
    assert new_login_resp.status_code == 200


async def test_crawler_product_ingest_persists_product_with_typesense_stub(
    ac: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "DEV_API_KEY", "integration-key")
    monkeypatch.setattr(
        "app.handlers.handler_product._build_typesense_client",
        lambda: _FakeTypesenseClient(),
    )

    response = await ac.post(
        "/api/v1/crawler/products",
        headers={"X-API-Key": "integration-key"},
        json={
            "normalized_name": "Integration Phone 1",
            "product_name": "Integration Phone 1 256GB",
            "slug": "integration-phone-1",
            "brand": "Integration",
            "category": "Phones",
            "main_image_url": "https://example.com/integration-phone.jpg",
        },
    )
    assert response.status_code == 200
    product = response.json()
    assert product["normalized_name"] == "Integration Phone 1"

    list_resp = await ac.get("/api/v1/products/")
    assert list_resp.status_code == 200
    assert any(item["id"] == product["id"] for item in list_resp.json())


async def test_crawler_platform_product_ingest_creates_price_history(
    ac: AsyncClient,
    created_platform: dict,
    created_product: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "DEV_API_KEY", "integration-key")

    ingest_resp = await ac.post(
        "/api/v1/crawler/platform-products",
        headers={"X-API-Key": "integration-key"},
        json=[
            {
                "product_id": created_product["id"],
                "platform_id": created_platform["id"],
                "raw_name": "Integration Phone - Marketplace",
                "original_item_id": "integration-phone-001",
                "url": "https://example.com/integration-phone-001",
                "affiliate_url": "https://example.com/integration-phone-001?aff=1",
                "current_price": 21000000,
                "original_price": 25000000,
                "in_stock": True,
            }
        ],
    )
    assert ingest_resp.status_code == 200
    platform_product = ingest_resp.json()[0]

    by_product_resp = await ac.get(
        "/api/v1/platform_products/platform-products/by-product-id"
        f"?product_id={created_product['id']}"
    )
    assert by_product_resp.status_code == 200
    assert any(item["id"] == platform_product["id"] for item in by_product_resp.json())

    records_resp = await ac.get(
        f"/api/v1/price_record/price-records/{platform_product['id']}"
    )
    assert records_resp.status_code == 200
    assert len(records_resp.json()) == 1
    assert float(records_resp.json()[0]["price"]) == 21000000


async def test_wishlist_add_duplicate_delete_flow(
    ac: AsyncClient,
    created_product: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    _patch_password_hashing(monkeypatch)
    auth_headers = await _register_and_login(
        ac,
        "integration-wishlist@example.com",
        "WishList@1234",
    )
    product_id = created_product["id"]

    first_add_resp = await ac.post(
        "/api/v1/wish_lists/",
        headers=auth_headers,
        json={"product_id": product_id},
    )
    assert first_add_resp.status_code == 200

    duplicate_add_resp = await ac.post(
        "/api/v1/wish_lists/",
        headers=auth_headers,
        json={"product_id": product_id},
    )
    assert duplicate_add_resp.status_code == 200
    matching_items = [
        item
        for item in duplicate_add_resp.json()["items"]
        if item["product_id"] == product_id
    ]
    assert len(matching_items) == 1

    delete_resp = await ac.delete(f"/api/v1/wish_lists/{product_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    list_resp = await ac.get("/api/v1/wish_lists/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert product_id not in [item["product_id"] for item in list_resp.json()["items"]]


async def test_price_alert_triggers_against_current_platform_price(
    ac: AsyncClient,
    created_product: dict,
    created_platform_product: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    _patch_password_hashing(monkeypatch)
    auth_headers = await _register_and_login(
        ac,
        "integration-alert@example.com",
        "Alert@1234",
    )
    sent_emails = []

    async def _fake_send_price_drop_email_async(**kwargs):
        sent_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.price_alert.send_price_drop_email_async",
        _fake_send_price_drop_email_async,
    )

    product_id = created_product["id"]
    create_resp = await ac.post(
        "/api/v1/price_alerts/",
        headers=auth_headers,
        json={"product_id": product_id, "target_price": 30000000},
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["status"] == 0

    trigger_resp = await ac.post(
        "/api/v1/price_alerts/trigger",
        headers=auth_headers,
        json={"product_id": product_id},
    )
    assert trigger_resp.status_code == 200
    assert trigger_resp.json()["checked_products"] == 1
    assert trigger_resp.json()["triggered_alerts"] == 1

    alerts_resp = await ac.get("/api/v1/price_alerts/", headers=auth_headers)
    assert alerts_resp.status_code == 200
    assert alerts_resp.json()[0]["status"] == 1


async def test_trending_deals_uses_price_history_and_current_price(
    ac: AsyncClient,
    created_platform_product: dict,
):
    platform_product_id = created_platform_product["id"]

    for price in (35000000, 34000000):
        response = await ac.post(
            "/api/v1/price_record/price-records",
            json={
                "platform_product_id": platform_product_id,
                "price": price,
                "original_price": 36000000,
            },
        )
        assert response.status_code == 201

    trending_resp = await ac.get(
        "/api/v1/platform_products/platform-products/trending?limit=10"
    )
    assert trending_resp.status_code == 200
    deal_ids = [item["id"] for item in trending_resp.json()]
    assert platform_product_id in deal_ids
