# app/api/products.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.product import Product
from server.app.schemas.product import ProductResponse

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