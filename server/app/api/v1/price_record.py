from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.price_record import PriceRecord 
from app.schemas.price_record import PriceRecordResponse
from app.models.platform_product import PlatformProduct

router = APIRouter()

@router.get(
    "/price-records",
    response_model=List[PriceRecordResponse],
    status_code=status.HTTP_200_OK
)
async def get_all_price_records(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Lấy danh sách lịch sử giá (Phân trang)
    """
    # 1. Tạo câu lệnh select, sắp xếp theo thời gian mới nhất
    stmt = (
        select(PriceRecord)
        .order_by(PriceRecord.recorded_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    # 2. Thực thi
    result = await db.execute(stmt)
    
    return result.scalars().all()

@router.get(
    "/price-records/{product_id}",
    response_model=List[PriceRecordResponse]
)
async def get_price_record_by_platform_product_id(
    platform_product_id: str, # UUID truyền vào từ URL
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy lịch sử giá của 1 sản phẩm cụ thể
    """
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.platform_product_id == platform_product_id)
        .order_by(PriceRecord.recorded_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_price_record(
    db: AsyncSession, 
    platform_product: PlatformProduct, 
    payload_dict: dict
):
    """
    Tạo một bản ghi lịch sử giá cho Platform Product.
    """
    price_record = PriceRecord(
        platform_product_id=platform_product.id,
        price=payload_dict.get("current_price"),
        original_price=payload_dict.get("original_price"),
        is_flash_sale=payload_dict.get("is_flash_sale", False),
        # recorded_at sẽ sử dụng server_default=func.now() nếu không truyền
    )
    db.add(price_record)
    return price_record