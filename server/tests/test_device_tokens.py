import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user_device_token import UserDeviceToken
from tests.conftest import TestingSessionLocal, _register_and_login


@pytest.mark.asyncio
async def test_register_device_token_requires_auth(ac: AsyncClient):
    response = await ac.post("/api/v1/device_tokens/", json={"token": "fcm-token"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_user_can_register_and_update_device_token(
    ac: AsyncClient,
    auth_headers: dict,
):
    response = await ac.post(
        "/api/v1/device_tokens/",
        json={"token": "fcm-token-1", "platform": "android"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "fcm-token-1"
    assert data["platform"] == "android"
    assert data["is_active"] is True

    update_response = await ac.post(
        "/api/v1/device_tokens/",
        json={"token": "fcm-token-1", "platform": "ANDROID"},
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    async with TestingSessionLocal() as db:
        rows = (await db.execute(select(UserDeviceToken))).scalars().all()

    assert len(rows) == 1
    assert rows[0].is_active is True
    assert rows[0].platform == "android"


@pytest.mark.asyncio
async def test_authenticated_user_can_deactivate_own_device_token(
    ac: AsyncClient,
    auth_headers: dict,
):
    await ac.post(
        "/api/v1/device_tokens/",
        json={"token": "logout-token", "platform": "android"},
        headers=auth_headers,
    )

    response = await ac.delete("/api/v1/device_tokens/logout-token", headers=auth_headers)

    assert response.status_code == 200
    async with TestingSessionLocal() as db:
        token = (
            await db.execute(select(UserDeviceToken).where(UserDeviceToken.token == "logout-token"))
        ).scalar_one()

    assert token.is_active is False


@pytest.mark.asyncio
async def test_user_cannot_deactivate_another_users_device_token(
    ac: AsyncClient,
    auth_headers: dict,
):
    other_headers = await _register_and_login(
        ac,
        email="other-device-user@example.com",
        password="Other@1234",
        full_name="Other User",
    )
    await ac.post(
        "/api/v1/device_tokens/",
        json={"token": "other-token", "platform": "android"},
        headers=other_headers,
    )

    response = await ac.delete("/api/v1/device_tokens/other-token", headers=auth_headers)

    assert response.status_code == 404
    async with TestingSessionLocal() as db:
        token = (
            await db.execute(select(UserDeviceToken).where(UserDeviceToken.token == "other-token"))
        ).scalar_one()

    assert token.is_active is True
