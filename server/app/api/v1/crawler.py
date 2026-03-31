from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_dev_api_key
from app.db.session import get_db
from app.models.platform import Platform
from app.models.platform_product import PlatformProduct
from app.handlers.handler_product import upsert_product
from app.api.v1.price_record import create_price_record

from app.schemas.crawler import (
    PlatformProductIngestRequest,
    PlatformProductIngestResponse,
    ProductIngestRequest,
    ProductIngestResponse,
)

router = APIRouter(dependencies=[Depends(require_dev_api_key)])


@router.post(
    "/products",
    response_model=ProductIngestResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_product(
    payload: ProductIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    #! Se can nhac sau (VINH KHONG DUOC SUA)
    return await upsert_product(payload=payload, db=db)


@router.post(
    "/platform-products", 
    response_model=List[PlatformProductIngestResponse], 
    status_code=status.HTTP_200_OK,
)
async def upload_platform_products_bulk(
    payload: List[PlatformProductIngestRequest],
    db: AsyncSession = Depends(get_db),
):
    results = []
    try:
        for item in payload:
            stmt = select(PlatformProduct).where(
                and_(
                    PlatformProduct.platform_id == item.platform_id,
                    PlatformProduct.original_item_id == item.original_item_id,
                )
            )
            result = await db.execute(stmt)
            platform_product = result.scalar_one_or_none()

            payload_dict = item.model_dump()
            if payload_dict.get("last_crawled_at") is None:
                payload_dict["last_crawled_at"] = datetime.now(timezone.utc)

            if platform_product is None:
                platform_product = PlatformProduct(**payload_dict)
                db.add(platform_product)
            else:
                for field, value in payload_dict.items():
                    setattr(platform_product, field, value)
            
            # Flush để lấy ID (nếu là insert) trước khi tạo PriceRecord
            await db.flush()

            # 3. Luôn tạo PriceRecord mới để lưu lịch sử giá tại thời điểm crawl
            await create_price_record(db, platform_product, payload_dict)

            results.append(platform_product)

        # 4. Lưu tất cả vào DB
        await db.commit()

        # 5. Refresh nếu cần dữ liệu mới nhất (như ID, timestamps)
        for p in results:
            await db.refresh(p)

    except Exception as e:
        await db.rollback()
        raise e
    return results
