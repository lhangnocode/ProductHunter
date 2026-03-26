from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.platform import Platform
from app.schemas.platform import PlatformCreateRequest, PlatformResponse

router = APIRouter()

@router.post("/", response_model=PlatformResponse, status_code=status.HTTP_201_CREATED)
async def create_platform(
    platform_in: PlatformCreateRequest,
    db: AsyncSession = Depends(get_db)
):
   
    # Khởi tạo object từ schema
    new_platform = Platform(
        name=platform_in.name,
        base_url=platform_in.base_url,
        affiliate_config=platform_in.affiliate_config
    )
    
    # Push vào database (Môi trường Async)
    db.add(new_platform)
    await db.commit()
    await db.refresh(new_platform) # Cập nhật lại object để lấy ID (SERIAL) vừa sinh ra
    
    return new_platform

@router.get("/", response_model=List[PlatformResponse])
async def get_platforms(db: AsyncSession = Depends(get_db)):
    """
    Lấy danh sách toàn bộ các nền tảng đang có.
    """
    stmt = select(Platform)
    result = await db.execute(stmt)
    return result.scalars().all()