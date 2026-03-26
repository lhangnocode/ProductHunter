from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ProductPriceBase(BaseModel):
    platform: str
    price: float
    currency: str = "VND"
    product_url: str
    seller: Optional[str] = None
    in_stock: int = 1


class ProductPriceResponse(ProductPriceBase):
    id: int
    product_id: int
    crawled_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    normalized_name: str
    normalized_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    id: UUID
    normalized_name: Optional[str] = None
    created_at: datetime
    prices: List[ProductPriceResponse] = []

    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    total: int
    items: List[ProductResponse]
