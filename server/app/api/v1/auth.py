# app/api/v1/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_premium_user
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user as user_service
from app.core.security import verify_password, create_access_token
from app.core.config import settings

router = APIRouter()


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

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
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