from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.platform import PlatformPriceItem

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
    # Đã xóa dòng normalized_name bị trùng
    
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: UUID
    # Đã xóa dòng id bị trùng
    created_at: datetime
    prices: List[ProductPriceResponse] = []

    class Config:
        from_attributes = True

class ProductSearchResponse(BaseModel):
    total: int
    items: List[ProductResponse]


class ProductCompareGroup(BaseModel):
    id: UUID
    normalized_name: str
    slug: str
    main_image_url: Optional[str] = None
    lowest_price: Optional[float] = None 
    platforms: List[PlatformPriceItem]

class SearchCompareResponse(BaseModel):
    keyword: str
    total_results: int
    data: List[ProductCompareGroup]
=======

class ProductSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    normalized_name: str
    slug: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None
    created_at: datetime

