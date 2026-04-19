"""
Test suite cho Social Auth API: /api/v1/auth/social/
Bao gồm: kiểm tra provider validation, unsupported provider.
Lưu ý: OAuth redirect và callback không thể test đầy đủ vì cần
provider thật (Google, GitHub). Chỉ test được logic validation.
"""
import pytest
from httpx import AsyncClient


# ============================================================
# SOCIAL LOGIN — GET /api/v1/auth/social/{provider}/login
# ============================================================
@pytest.mark.asyncio
async def test_social_login_unsupported_provider(ac: AsyncClient):
    """Provider không hỗ trợ → 400."""
    response = await ac.get("/api/v1/auth/social/facebook/login")
    assert response.status_code == 400
    assert "không được hỗ trợ" in response.json()["detail"]


@pytest.mark.asyncio
async def test_social_login_empty_provider(ac: AsyncClient):
    """Provider rỗng → 400 hoặc 404."""
    response = await ac.get("/api/v1/auth/social//login")
    # FastAPI sẽ trả 404 vì path không match
    assert response.status_code in (400, 404)


# ============================================================
# SOCIAL CALLBACK — GET /api/v1/auth/social/{provider}/callback
# ============================================================
@pytest.mark.asyncio
async def test_social_callback_unsupported_provider(ac: AsyncClient):
    """Provider không hỗ trợ trong callback → 400."""
    response = await ac.get("/api/v1/auth/social/twitter/callback")
    assert response.status_code == 400
    assert "không hợp lệ" in response.json()["detail"]


@pytest.mark.asyncio
async def test_social_callback_google_no_state(ac: AsyncClient):
    """Google callback thiếu state/code → lỗi (400/500).
    OAuth provider sẽ reject vì thiếu authorization code."""
    response = await ac.get("/api/v1/auth/social/google/callback")
    # Sẽ lỗi vì không có state/code params từ Google
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_social_callback_github_no_code(ac: AsyncClient):
    """GitHub callback thiếu code → lỗi."""
    response = await ac.get("/api/v1/auth/social/github/callback")
    assert response.status_code >= 400
