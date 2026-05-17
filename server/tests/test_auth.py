"""
Test suite cho Auth API: /api/v1/auth/
Bao gồm: register, login, get me, refresh token, premium feature.
"""
import pytest
from httpx import AsyncClient
from app.core.security import create_password_reset_token


# ============================================================
# REGISTER
# ============================================================
@pytest.mark.asyncio
async def test_register_success(ac: AsyncClient):
    """Đăng ký tài khoản mới thành công."""
    response = await ac.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "NewUser@1234",
        "full_name": "New User",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(ac: AsyncClient):
    """Đăng ký trùng email phải trả về 400."""
    # Đăng ký lần 1
    await ac.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "Test@1234",
    })
    # Đăng ký lần 2 cùng email
    response = await ac.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "Other@5678",
    })
    assert response.status_code == 400
    assert "đã được đăng ký" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(ac: AsyncClient):
    """Email không hợp lệ phải trả về 422."""
    response = await ac.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Test@1234",
    })
    assert response.status_code == 422


# ============================================================
# LOGIN
# ============================================================
@pytest.mark.asyncio
async def test_login_success(ac: AsyncClient):
    """Đăng nhập đúng email/password → nhận token."""
    # Tạo user
    await ac.post("/api/v1/auth/register", json={
        "email": "loginuser@example.com",
        "password": "Login@1234",
    })
    # Đăng nhập (OAuth2PasswordRequestForm dùng form data)
    response = await ac.post("/api/v1/auth/login", data={
        "username": "loginuser@example.com",
        "password": "Login@1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(ac: AsyncClient):
    """Sai mật khẩu phải trả về 400."""
    await ac.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "Correct@1234",
    })
    response = await ac.post("/api/v1/auth/login", data={
        "username": "wrongpw@example.com",
        "password": "WrongPassword",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_nonexistent_email(ac: AsyncClient):
    """Email không tồn tại phải trả về 400."""
    response = await ac.post("/api/v1/auth/login", data={
        "username": "noone@example.com",
        "password": "Whatever@1234",
    })
    assert response.status_code == 400


# ============================================================
# GET /me
# ============================================================
@pytest.mark.asyncio
async def test_get_me_authenticated(ac: AsyncClient, auth_headers: dict):
    """Lấy profile khi đã login → 200 + thông tin user."""
    response = await ac.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(ac: AsyncClient):
    """Không gửi token → 401."""
    response = await ac.get("/api/v1/auth/me")
    assert response.status_code == 401


# ============================================================
# PREMIUM FEATURE
# ============================================================
@pytest.mark.asyncio
async def test_premium_feature_with_premium_user(ac: AsyncClient, premium_auth_headers: dict):
    """User Premium gọi premium-feature → 200."""
    response = await ac.post("/api/v1/auth/premium-feature", headers=premium_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_premium_feature_with_free_user(ac: AsyncClient, auth_headers: dict):
    """User Free gọi premium-feature → 403."""
    response = await ac.post("/api/v1/auth/premium-feature", headers=auth_headers)
    assert response.status_code == 403


# ============================================================
# REFRESH TOKEN
# ============================================================
@pytest.mark.asyncio
async def test_refresh_token_success(ac: AsyncClient):
    """Refresh token hợp lệ → nhận access token mới."""
    # Register + Login
    await ac.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "Refresh@1234",
    })
    login_resp = await ac.post("/api/v1/auth/login", data={
        "username": "refresh@example.com",
        "password": "Refresh@1234",
    })
    refresh_token = login_resp.json()["refresh_token"]

    # Gọi refresh
    response = await ac.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(ac: AsyncClient):
    """Token giả → 401."""
    response = await ac.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.fake.token",
    })
    assert response.status_code == 401


# ============================================================
# FORGOT / RESET PASSWORD
# ============================================================
@pytest.mark.asyncio
async def test_forgot_password_returns_generic_message(ac: AsyncClient):
    response = await ac.post("/api/v1/auth/forgot-password", json={
        "email": "unknown@example.com",
    })
    assert response.status_code == 200
    assert "gửi hướng dẫn" in response.json()["message"]


@pytest.mark.asyncio
async def test_reset_password_success(ac: AsyncClient):
    email = "resetok@example.com"
    old_password = "OldPass@1234"
    new_password = "NewPass@1234"

    await ac.post("/api/v1/auth/register", json={
        "email": email,
        "password": old_password,
    })

    token = create_password_reset_token(email)
    reset_resp = await ac.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": new_password,
    })
    assert reset_resp.status_code == 200

    old_login = await ac.post("/api/v1/auth/login", data={
        "username": email,
        "password": old_password,
    })
    assert old_login.status_code == 400

    new_login = await ac.post("/api/v1/auth/login", data={
        "username": email,
        "password": new_password,
    })
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(ac: AsyncClient):
    response = await ac.post("/api/v1/auth/reset-password", json={
        "token": "invalid.token.value",
        "new_password": "AnyPass@1234",
    })
    assert response.status_code == 400


# ============================================================
# VERIFY CLEANUP — chứng minh data bị xóa giữa các test
# ============================================================
@pytest.mark.asyncio
async def test_data_is_cleaned_between_tests(ac: AsyncClient):
    """
    Test này chạy sau các test register ở trên.
    Nếu cleanup hoạt động đúng, user 'newuser@example.com'
    không còn tồn tại → đăng ký lại thành công.
    """
    response = await ac.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "NewUser@1234",
        "full_name": "New User Again",
    })
    assert response.status_code == 200, "Cleanup không hoạt động — email vẫn tồn tại!"
