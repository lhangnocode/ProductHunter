from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenResponse
from app.services import device_token as device_token_service

router = APIRouter()


@router.post("/", response_model=DeviceTokenResponse)
async def register_device_token(
    token_in: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await device_token_service.upsert_device_token(db, current_user.id, token_in)


@router.delete("/{token:path}", status_code=status.HTTP_200_OK)
async def remove_device_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await device_token_service.deactivate_device_token(db, current_user.id, token)
    return {"message": "Device token deactivated"}
