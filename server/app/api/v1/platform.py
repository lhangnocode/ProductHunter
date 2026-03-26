from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.platform import Platform
from app.schemas.schema_crawler import PlatformResponse

router = APIRouter()

@router.get(
    "/platforms/all_platforms",
    response_model=List[PlatformResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_platforms(
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy toàn bộ danh sách các sàn thương mại điện tử (Lazada, Shopee, Tiki...).
    Dữ liệu trả về bao gồm ID, tên sàn, link gốc và cấu hình affiliate.
    """

    stmt = select(Platform).order_by(Platform.id.asc())
    
    result = await db.execute(stmt)
    
    platforms = result.scalars().all()
    
    return platforms