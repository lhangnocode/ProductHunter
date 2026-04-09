import secrets
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.user import User
from sqlalchemy import select

router = APIRouter()
oauth = OAuth()

# Cấu hình Google
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Cấu hình GitHub
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# 1. API chuyển hướng người dùng sang trang đăng nhập của Google/Github
@router.get("/{provider}/login")
async def social_login(provider: str, request: Request):
    client = oauth.create_client(provider)
    redirect_uri = f"https://nanopi-r5c.tail47f64f.ts.net/api/v1/auth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


# 2. API nhận callback trả về từ Google/Github
@router.get("/{provider}/callback")
async def social_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    
    # Lấy thông tin user
    if provider == 'google':
        user_info = token.get('userinfo')
        email = user_info.get('email')
        full_name = user_info.get('name')
    elif provider == 'github':
        resp = await client.get('user', token=token)
        user_info = resp.json()
        full_name = user_info.get('name') or user_info.get('login')
        # GitHub có thể ẩn email, phải gọi API riêng để lấy
        email_resp = await client.get('user/emails', token=token)
        emails = email_resp.json()
        email = next((e['email'] for e in emails if e['primary']), emails[0]['email'])

    # Kiểm tra user trong DB
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Nếu user chưa tồn tại -> Tự động đăng ký
    if not user:
        random_password = secrets.token_urlsafe(16)
        user = User(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(random_password),
            plan=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Tạo JWT Tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Chuyển hướng về Frontend kèm theo token trên URL
    frontend_redirect_url = f"{settings.FRONTEND_URL}/?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=frontend_redirect_url)