from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_dev_api_key
from app.db.session import get_db
from app.models.model_product import Platform, PlatformProduct, Product
from app.schemas.schema_crawler import (
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
    stmt = select(Product).where(Product.slug == payload.slug)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        product = Product(**payload.model_dump())
        db.add(product)
    else:
        for field, value in payload.model_dump().items():
            setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.post(
    "/platform-products",
    response_model=PlatformProductIngestResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_platform_product(
    payload: PlatformProductIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(select(Product.id).where(Product.id == payload.product_id))
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist")

    platform_result = await db.execute(select(Platform.id).where(Platform.id == payload.platform_id))
    if platform_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform does not exist")

    stmt = select(PlatformProduct).where(
        and_(
            PlatformProduct.platform_id == payload.platform_id,
            PlatformProduct.original_item_id == payload.original_item_id,
        )
    )
    result = await db.execute(stmt)
    platform_product = result.scalar_one_or_none()

    payload_dict = payload.model_dump()
    if payload_dict["last_crawled_at"] is None:
        payload_dict["last_crawled_at"] = datetime.now(timezone.utc)

    if platform_product is None:
        platform_product = PlatformProduct(**payload_dict)
        db.add(platform_product)
    else:
        for field, value in payload_dict.items():
            setattr(platform_product, field, value)

    await db.commit()
    await db.refresh(platform_product)
    return platform_product
