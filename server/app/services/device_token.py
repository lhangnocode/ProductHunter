from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.user_device_token import UserDeviceToken
from app.schemas.device_token import DeviceTokenCreate


async def upsert_device_token(
    db: AsyncSession,
    user_id: UUID,
    token_in: DeviceTokenCreate,
) -> UserDeviceToken:
    token_value = token_in.token.strip()
    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Device token cannot be empty",
        )

    platform = token_in.platform.strip().lower() or "android"
    result = await db.execute(
        select(UserDeviceToken).where(UserDeviceToken.token == token_value)
    )
    row = result.scalar_one_or_none()

    if row is None:
        row = UserDeviceToken(
            user_id=user_id,
            token=token_value,
            platform=platform,
            is_active=True,
        )
        db.add(row)
    else:
        row.user_id = user_id
        row.platform = platform
        row.is_active = True
        row.last_seen_at = func.now()

    await db.commit()
    await db.refresh(row)
    return row


async def deactivate_device_token(db: AsyncSession, user_id: UUID, token: str) -> None:
    token_value = token.strip()
    result = await db.execute(
        select(UserDeviceToken).where(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.token == token_value,
            UserDeviceToken.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device token not found",
        )

    row.is_active = False
    await db.commit()
