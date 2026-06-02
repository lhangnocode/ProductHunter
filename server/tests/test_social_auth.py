"""
Test suite cho Social Auth API: /api/v1/auth/
Bao gồm: kiểm tra provider validation, unsupported provider.
Lưu ý: OAuth redirect và callback không thể test đầy đủ vì cần
provider thật (Google, GitHub). Chỉ test được logic validation.
"""
import pytest
from authlib.integrations.base_client.errors import MismatchingStateError
from httpx import AsyncClient
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.api.v1 import social_auth
from app.models.user import User
from tests.conftest import TestingSessionLocal


class FakeOAuthResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class FakeOAuthClient:
    def __init__(self, token=None, user=None, emails=None):
        self.token = token or {}
        self.user = user or {}
        self.emails = emails or []
        self.redirects = []

    async def authorize_redirect(self, request, redirect_uri):
        self.redirects.append(redirect_uri)
        return RedirectResponse("https://provider.example.test/oauth")

    async def authorize_access_token(self, request):
        return self.token

    async def get(self, path, token):
        if path == "user":
            return FakeOAuthResponse(self.user)
        if path == "user/emails":
            return FakeOAuthResponse(self.emails)
        raise AssertionError(f"unexpected oauth path: {path}")


async def _user_count(email: str) -> int:
    async with TestingSessionLocal() as db:
        return await db.scalar(select(func.count(User.id)).where(User.email == email))


# ============================================================
# SOCIAL LOGIN — GET /api/v1/auth/{provider}/login
# ============================================================
@pytest.mark.asyncio
async def test_social_login_unsupported_provider(ac: AsyncClient):
    """Provider không hỗ trợ → 400."""
    response = await ac.get("/api/v1/auth/facebook/login")
    assert response.status_code == 400
    assert "không được hỗ trợ" in response.json()["detail"]


@pytest.mark.asyncio
async def test_social_login_empty_provider(ac: AsyncClient):
    """Provider rỗng → 400 hoặc 404."""
    response = await ac.get("/api/v1/auth//login")
    # FastAPI sẽ trả 404 vì path không match
    assert response.status_code in (400, 404)


@pytest.mark.asyncio
async def test_social_login_google_redirect(monkeypatch: pytest.MonkeyPatch, ac: AsyncClient):
    fake_client = FakeOAuthClient()
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/google/login")

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "https://provider.example.test/oauth"
    assert fake_client.redirects[0].endswith("/api/v1/auth/google/callback")


@pytest.mark.asyncio
async def test_social_login_github_redirect(monkeypatch: pytest.MonkeyPatch, ac: AsyncClient):
    fake_client = FakeOAuthClient()
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/github/login")

    assert response.status_code in (302, 307)
    assert fake_client.redirects[0].endswith("/api/v1/auth/github/callback")


@pytest.mark.asyncio
async def test_social_login_allowed_frontend_url_sets_cookie(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: FakeOAuthClient())

    response = await ac.get(
        "/api/v1/auth/google/login?frontend_url=http://localhost:3000/"
    )

    assert response.cookies["frontend_url"].strip('"') == "http://localhost:3000"


@pytest.mark.asyncio
async def test_social_login_disallowed_frontend_url_does_not_set_cookie(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: FakeOAuthClient())

    response = await ac.get(
        "/api/v1/auth/google/login?frontend_url=https://evil.example.test"
    )

    assert "set-cookie" not in response.headers


# ============================================================
# SOCIAL CALLBACK — GET /api/v1/auth/{provider}/callback
# ============================================================
@pytest.mark.asyncio
async def test_social_callback_unsupported_provider(ac: AsyncClient):
    """Provider không hỗ trợ trong callback → 400."""
    response = await ac.get("/api/v1/auth/twitter/callback")
    assert response.status_code == 400
    assert "không hợp lệ" in response.json()["detail"]


@pytest.mark.asyncio
async def test_social_callback_google_no_state(ac: AsyncClient):
    """Google callback thiếu state/code → lỗi (400/500).
    OAuth provider sẽ reject vì thiếu authorization code."""
    with pytest.raises(MismatchingStateError):
        await ac.get("/api/v1/auth/google/callback")


@pytest.mark.asyncio
async def test_social_callback_github_no_code(ac: AsyncClient):
    """GitHub callback thiếu code → lỗi."""
    with pytest.raises(MismatchingStateError):
        await ac.get("/api/v1/auth/github/callback")


@pytest.mark.asyncio
async def test_social_callback_google_creates_user_and_redirects(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    email = "google-new@example.com"
    fake_client = FakeOAuthClient(
        token={"userinfo": {"email": email, "name": "Google User"}},
    )
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/google/callback")

    assert response.status_code in (302, 307)
    assert "access_token=" in response.headers["location"]
    assert "refresh_token=" in response.headers["location"]
    assert await _user_count(email) == 1


@pytest.mark.asyncio
async def test_social_callback_google_existing_user_not_duplicated(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    email = "google-existing@example.com"
    fake_client = FakeOAuthClient(
        token={"userinfo": {"email": email, "name": "Google User"}},
    )
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    await ac.get("/api/v1/auth/google/callback")
    response = await ac.get("/api/v1/auth/google/callback")

    assert response.status_code in (302, 307)
    assert await _user_count(email) == 1


@pytest.mark.asyncio
async def test_social_callback_github_uses_primary_email(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    fake_client = FakeOAuthClient(
        user={"name": None, "login": "octo"},
        emails=[
            {"email": "secondary@example.com", "primary": False},
            {"email": "primary@example.com", "primary": True},
        ],
    )
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/github/callback")

    assert response.status_code in (302, 307)
    assert await _user_count("primary@example.com") == 1
    assert await _user_count("secondary@example.com") == 0


@pytest.mark.asyncio
async def test_social_callback_github_falls_back_to_first_email(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    fake_client = FakeOAuthClient(
        user={"name": "Octo Cat", "login": "octo"},
        emails=[
            {"email": "first@example.com", "primary": False},
            {"email": "second@example.com", "primary": False},
        ],
    )
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/github/callback")

    assert response.status_code in (302, 307)
    assert await _user_count("first@example.com") == 1


@pytest.mark.asyncio
async def test_social_callback_no_email_returns_400(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
):
    fake_client = FakeOAuthClient(token={"userinfo": {"name": "No Email"}})
    monkeypatch.setattr(social_auth.oauth, "create_client", lambda provider: fake_client)

    response = await ac.get("/api/v1/auth/google/callback")

    assert response.status_code == 400
    assert "Không thể lấy được email" in response.json()["detail"]
