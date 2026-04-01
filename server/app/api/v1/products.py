# app/api/products.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductCompareGroup, ProductResponse, SearchCompareResponse
from app.schemas.platform import PlatformPriceItem
from sqlalchemy.orm import selectinload

router = APIRouter()

@router.get("/search", response_model=List[ProductResponse])
async def search_products( 
    name: str = Query(..., description="Name Product pro..."),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Product).where(Product.normalized_name.ilike(f"%{name}%"))
    result = await db.execute(stmt)
    products = result.scalars().all()
    return products

@router.get("/")
async def get_all_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return products



@router.get("/compare",
             response_model=SearchCompareResponse,
)
async def search_and_compare_products(
    q: str = Query(..., min_length=2, description="Từ khóa tìm kiếm"),
    db: AsyncSession = Depends(get_db),
):

    stmt = (
        select(Product)
        .options(selectinload(Product.platform_products)) 
        .where(Product.normalized_name.ilike(f"%{q}%"))
        .order_by(Product.created_at.desc())
    )
    
    result = await db.execute(stmt)
    products = result.scalars().all()

    response_list = []
    
    for product in products:
        platforms_data = []
        valid_prices = []
        for pp in product.platform_products:
            platforms_data.append(
                PlatformPriceItem(
                    platform_id=pp.platform_id,
                    url=pp.url,
                    affiliate_url=pp.affiliate_url,
                    current_price=pp.current_price,
                    original_price=pp.original_price,
                    in_stock=pp.in_stock,
                    last_crawled_at=pp.last_crawled_at
                )
            )
            if pp.in_stock and pp.current_price is not None:
                valid_prices.append(pp.current_price)

        lowest_price = min(valid_prices) if valid_prices else None
        response_list.append(
            ProductCompareGroup(
                id=product.id,
                normalized_name=product.normalized_name,
                slug=product.slug,
                main_image_url=product.main_image_url,
                lowest_price=lowest_price,
                platforms=platforms_data
            )
        )


    response_list.sort(key=lambda x: x.lowest_price if x.lowest_price is not None else float('inf'))

    return SearchCompareResponse(
        keyword=q,
        total_results=len(response_list),
        data=response_list
    )