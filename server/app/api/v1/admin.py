from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


class UserPlanUpdate(BaseModel):
    plan: int = Field(..., ge=0, le=1)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/users/{user_id}/plan", response_model=UserResponse)
async def update_user_plan(
    user_id: UUID,
    payload: UserPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.plan = payload.plan
    await db.commit()
    await db.refresh(user)
    return user
