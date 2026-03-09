from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_db
from app.models.model_product import Product
from app.schemas.schema_product import ProductResponse, ProductCreate, ProductSearchResponse

router = APIRouter()

@router.get("/", response_model=ProductSearchResponse)
async def list_products():
    return None

