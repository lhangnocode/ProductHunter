# app/api/products.py
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductResponse, ProductSearchResponse, SearchPaginatedResponse

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


    

@router.get("/searchAll", response_model=SearchPaginatedResponse)
async def search_products_list(
    q: str = Query(..., min_length=2, description="Keyword"),
    page: int = Query(1, ge=1, description="current page"),
    limit: int = Query(20, ge=1, le=100, description="num of products per page"),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count(Product.id)).where(Product.normalized_name.ilike(f"%{q}%"))
    total_results = await db.scalar(count_stmt)
    total_pages = math.ceil(total_results / limit) if total_results > 0 else 0
    offset = (page - 1) * limit

    if total_results > 0:
        stmt = (
            select(Product)
            .where(Product.normalized_name.ilike(f"%{q}%"))
            .order_by(Product.created_at.desc()) 
            .offset(offset)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        products = result.scalars().all()
    else:
        products = [] 

    return {
        "keyword": q,
        "current_page": page,
        "total_pages": total_pages,
        "total_results": total_results,
        "data": products 
    }