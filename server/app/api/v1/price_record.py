from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.price_record import PriceRecord 
from app.schemas.price_record import PriceRecordResponse
from app.models.platform_product import PlatformProduct
from app.handlers.handler_price_record import analyze_price_status
from app.schemas.price_record import PriceRecordCreateRequest, PriceRecordResponse
from app.models.price_record import PriceRecord

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
    "/price-records/{platform_product_id}",
    response_model=List[PriceRecordResponse]
)
async def get_price_record_by_platform_product_id(
    platform_product_id: UUID, # UUID truyền vào từ URL
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy lịch sử giá của 1 sản phẩm cụ thể
    """
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.platform_product_id == platform_product_id)
        .order_by(PriceRecord.recorded_at.asc())
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


@router.post(
    "/price-records",
    response_model=PriceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def push_price_record(
    payload: PriceRecordCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PlatformProduct).where(PlatformProduct.id == payload.platform_product_id)
    result = await db.execute(stmt)
    platform_product = result.scalar_one_or_none()
    if platform_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PlatformProduct not found")

    pr = PriceRecord(
        platform_product_id=payload.platform_product_id,
        price=payload.price,
        original_price=payload.original_price,
        is_flash_sale=payload.is_flash_sale,
    )
    if payload.recorded_at is not None:
        pr.recorded_at = payload.recorded_at

    db.add(pr)
    await db.commit()
    await db.refresh(pr)

    return pr


@router.post(
    "/price-records/batch",
    response_model=List[PriceRecordResponse],
    status_code=status.HTTP_201_CREATED,
)
async def push_price_records_batch(
    payload: List[PriceRecordCreateRequest],
    db: AsyncSession = Depends(get_db),
):
    created: List[PriceRecord] = []

    for item in payload:
        stmt = select(PlatformProduct).where(PlatformProduct.id == item.platform_product_id)
        result = await db.execute(stmt)
        platform_product = result.scalar_one_or_none()
        if platform_product is None:
            continue

        pr = PriceRecord(
            platform_product_id=item.platform_product_id,
            price=item.price,
            original_price=item.original_price,
            is_flash_sale=bool(item.is_flash_sale),
        )
        if item.recorded_at is not None:
            pr.recorded_at = item.recorded_at

        db.add(pr)
        created.append(pr)

    if not created:
        return []
    await db.commit()
    
    for pr in created:
        await db.refresh(pr)

    return created


@router.get("/price-analysis/{platform_product_id}")
async def get_price_analysis(
    platform_product_id: str, 
    current_price: float, 
    original_price: float, 
    db: AsyncSession = Depends(get_db)
):
    return await analyze_price_status(db, platform_product_id, current_price, original_price)