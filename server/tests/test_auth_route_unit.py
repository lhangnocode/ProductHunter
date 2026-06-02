from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import HTTPException

from app.api.v1 import auth as auth_api
from app.core.security import get_password_hash
from app.schemas.user import ForgotPasswordRequest, ResetPasswordRequest, UserCreate


@pytest.mark.asyncio
async def test_register_route_creates_user_when_email_unused(monkeypatch: pytest.MonkeyPatch):
    created_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="new@example.com",
        full_name="New User",
        plan=0,
    )
    monkeypatch.setattr(auth_api.user_service, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_api.user_service, "create_user", AsyncMock(return_value=created_user))

    result = await auth_api.register(
        UserCreate(email="new@example.com", password="NewUser@1234", full_name="New User"),
        db=AsyncMock(),
    )

    assert result.email == "new@example.com"
    auth_api.user_service.create_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_route_rejects_duplicate_email(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        auth_api.user_service,
        "get_user_by_email",
        AsyncMock(return_value=SimpleNamespace(email="existing@example.com")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_api.register(
            UserCreate(email="existing@example.com", password="Existing@1234"),
            db=AsyncMock(),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_login_route_success_and_invalid_password(monkeypatch: pytest.MonkeyPatch):
    user = SimpleNamespace(id=uuid.uuid4(), password_hash=get_password_hash("Secret@1234"))
    monkeypatch.setattr(auth_api.user_service, "get_user_by_email", AsyncMock(return_value=user))
    form_data = SimpleNamespace(username="user@example.com", password="Secret@1234")

    result = await auth_api.login(form_data=form_data, db=AsyncMock())

    assert result["token_type"] == "bearer"
    assert "access_token" in result
    assert "refresh_token" in result

    form_data.password = "Wrong@1234"
    with pytest.raises(HTTPException) as exc_info:
        await auth_api.login(form_data=form_data, db=AsyncMock())

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_login_route_rejects_missing_user(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(auth_api.user_service, "get_user_by_email", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await auth_api.login(
            form_data=SimpleNamespace(username="missing@example.com", password="Secret@1234"),
            db=AsyncMock(),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_profile_and_premium_routes_return_current_user():
    user = SimpleNamespace(full_name="Premium User")

    assert await auth_api.get_my_profile(current_user=user) is user
    result = await auth_api.use_premium_feature(current_user=user)
    assert "Premium User" in result["message"]


@pytest.mark.asyncio
async def test_forgot_password_uses_token_fallback_when_frontend_url_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    user = SimpleNamespace(email="reset@example.com")
    sent = {}

    async def _fake_send(to_email: str, reset_link: str):
        sent["to_email"] = to_email
        sent["reset_link"] = reset_link

    monkeypatch.setattr(auth_api.user_service, "get_user_by_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_api, "send_password_reset_email_async", _fake_send)
    monkeypatch.setattr(auth_api.settings, "FRONTEND_URL", "")

    result = await auth_api.forgot_password(
        ForgotPasswordRequest(email="reset@example.com"),
        db=AsyncMock(),
    )

    assert result["message"] == "Reset password email sent successfully"
    assert sent["to_email"] == "reset@example.com"
    assert sent["reset_link"].startswith("token:")


@pytest.mark.asyncio
async def test_reset_password_route_success_direct(monkeypatch: pytest.MonkeyPatch):
    user = SimpleNamespace(email="reset@example.com", password_hash="old")
    db = AsyncMock()
    token = auth_api.create_password_reset_token("reset@example.com")
    monkeypatch.setattr(auth_api.user_service, "get_user_by_email", AsyncMock(return_value=user))

    result = await auth_api.reset_password(
        ResetPasswordRequest(token=token, new_password="NewPass@1234"),
        db=db,
    )

    assert result["message"] == "Đặt lại mật khẩu thành công."
    assert user.password_hash != "old"
    db.commit.assert_awaited_once()
