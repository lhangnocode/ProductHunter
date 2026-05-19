# app/api/v1/auth.py
import uuid
import logging
from datetime import timedelta
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_premium_user
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services import user as user_service
from app.services.email import send_password_reset_email_async
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    get_password_hash,
)
from app.core.config import settings
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký.")
    
    return await user_service.create_user(db=db, user_in=user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không đúng.")

    token_data = {"sub": str(user.id)}

    # 3. Tạo cả 2 token
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user = Depends(get_current_user)
):
    return current_user


@router.post("/premium-feature")
async def use_premium_feature(
    current_user = Depends(get_current_premium_user)
):
    return {
        "message": f"Chào {current_user.full_name}, bạn đang dùng tính năng Premium!"
    }

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    # SỬA: Nhận token từ Body request thay vì Query param
    refresh_token: str = Body(..., embed=True), 
   
    db: AsyncSession = Depends(get_db) 
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã refresh token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user: 
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Nếu hợp lệ, cấp Access Token mới
    new_access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Forgot password requested for email=%s", payload.email)
    user = await user_service.get_user_by_email(db, email=payload.email)
    if not user:
        logger.info("Forgot password lookup: email not found for email=%s", payload.email)
        raise HTTPException(status_code=404, detail="Email is not registered")

    logger.info("Forgot password lookup: email found for email=%s", payload.email)
    token = create_password_reset_token(payload.email)
    logger.info("Reset token generated for email=%s", payload.email)

    frontend_url = settings.FRONTEND_URL.rstrip("/") if settings.FRONTEND_URL else ""
    reset_link = f"{frontend_url}/reset-password?token={token}" if frontend_url else f"token:{token}"

    logger.info(
        "SMTP config loaded: MAIL_USERNAME=%s MAIL_FROM=%s MAIL_SERVER=%s MAIL_PORT=%s",
        settings.MAIL_USERNAME,
        settings.MAIL_FROM,
        settings.MAIL_SERVER,
        settings.MAIL_PORT,
    )
    logger.info("Attempting reset password email send for email=%s", payload.email)
    try:
        await send_password_reset_email_async(payload.email, reset_link)
        logger.info("Reset password email sent successfully for email=%s", payload.email)
    except Exception:
        logger.exception("Failed to send reset password email for email=%s", payload.email)
        raise HTTPException(status_code=500, detail="Failed to send reset password email")

    return {"message": "Reset password email sent successfully"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    invalid_token_error = HTTPException(status_code=400, detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")
    try:
        decoded = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = decoded.get("type")
        email = decoded.get("sub")
        if token_type != "password_reset" or not email:
            raise invalid_token_error
    except JWTError:
        raise invalid_token_error

    user = await user_service.get_user_by_email(db, email=email)
    if not user:
        raise invalid_token_error

    user.password_hash = get_password_hash(payload.new_password)
    await db.commit()

    return {"message": "Đặt lại mật khẩu thành công."}
