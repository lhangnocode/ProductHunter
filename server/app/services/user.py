from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate):
    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        email=user_in.email,
        password_hash=hashed_password,
        full_name=user_in.full_name,
        plan=0
    )

    db.add(db_user)

    await db.commit()
    await db.refresh(db_user)

    return db_user