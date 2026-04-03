from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_dev_api_key
from app.db.session import get_db
from app.models.platform import Platform
from app.models.platform_product import PlatformProduct
from app.handlers.handler_platformproduct import (
    get_platform_products_by_product_id,
    search_platform_products,
)
from app.handlers.handler_product import upsert_product

from app.schemas.crawler import PlatformProductIngestResponse

router = APIRouter()


@router.get(
    "/platform-products/search",
    response_model=List[PlatformProductIngestResponse],
    status_code=status.HTTP_200_OK,
)
async def search_platform_products_endpoint(
    name: str = Query(..., description="Product name or slug"),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    return await search_platform_products(name, db=db, limit=limit, page=page)


@router.get(
    "/platform-products/by-product-id",
    response_model=List[PlatformProductIngestResponse],
    status_code=status.HTTP_200_OK,
)
async def get_platform_products_by_product_id_endpoint(
    product_id: UUID = Query(..., description="Product UUID"),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    return await get_platform_products_by_product_id(
        product_id,
        db=db,
        limit=limit,
        page=page,
    )

@router.get(
    "/platform-products", 
    response_model=List[PlatformProductIngestResponse], 
    status_code=status.HTTP_200_OK,
)
async def get_all_platform_products(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=100, description="Số lượng bản ghi mỗi trang"),
    offset: int = Query(default=0, ge=0, description="Số lượng bản ghi bỏ qua")
):
    try:
        stmt = (
            select(PlatformProduct)
            .order_by(PlatformProduct.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        
        platform_products = result.scalars().all()

        return platform_products

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi truy vấn dữ liệu: {str(e)}"
        )