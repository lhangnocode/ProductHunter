import uuid

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.deps import get_current_premium_user, get_current_user, require_dev_api_key
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_require_dev_api_key_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "DEV_API_KEY", "expected")

    with pytest.raises(HTTPException) as exc_info:
        await require_dev_api_key(x_api_key="wrong")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_dev_api_key_rejects_missing_server_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "DEV_API_KEY", "")

    with pytest.raises(HTTPException) as exc_info:
        await require_dev_api_key(x_api_key="anything")

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_current_user_rejects_malformed_token():
    async with TestingSessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="bad.token.value", db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_sub():
    token = jwt.encode(
        {"type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    async with TestingSessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_user():
    token = create_access_token(data={"sub": str(uuid.uuid4())})

    async with TestingSessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_premium_user_rejects_free_user():
    user = User(email="free@example.com", password_hash="hash", full_name="Free", plan=0)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_premium_user(current_user=user)

    assert exc_info.value.status_code == 403
