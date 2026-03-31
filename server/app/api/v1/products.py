# app/api/products.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.handlers.handler_product import search_product
from app.models.product import Product
from app.schemas.product import ProductResponse

router = APIRouter()

@router.get("/search", response_model=List[ProductResponse])
async def search_products( 
    name: str = Query(..., description="Name Product pro..."),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    products = await search_product(name, db=db, limit=limit, page=page)
    return products

@router.get("/")
async def get_all_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return products
