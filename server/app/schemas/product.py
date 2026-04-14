
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Optional, List
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
    product_name: Optional[str] = None
   
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass


class PlatformProductResponse(BaseModel):
    id: UUID
    product_id: UUID
    raw_name: Optional[str] = None
    platform: str
    price: Optional[float] = None
    url: Optional[str] = None

    @field_validator("platform", mode="before")
    @classmethod
    def extract_platform_name(cls, v: Any) -> str:
        if hasattr(v, "name"):
            return v.name
        return str(v)
    model_config = ConfigDict(from_attributes=True)

class ProductResponse(BaseModel):
    id: UUID
    normalized_name: str
    product_name: Optional[str] = None
    slug: str
    main_image_url: Optional[str] = None
    

    model_config = ConfigDict(from_attributes=True)

class SearchPaginatedResponse(BaseModel):
    keyword: str
    current_page: int
    total_pages: int
    total_results: int
    data: List[ProductResponse]

class ProductSearchResponse(BaseModel):
    total: int
    items: List[ProductResponse]


class ProductCompareGroup(BaseModel):
    id: UUID
    normalized_name: str
    product_name: Optional[str] = None
    slug: Optional[str] = None
    main_image_url: Optional[str] = None
    lowest_price: Optional[float] = None 
    platforms: List[PlatformPriceItem]

class SearchCompareResponse(BaseModel):
    keyword: str
    total_results: int
    data: List[ProductCompareGroup]


class ProductSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    normalized_name: str
    product_name: Optional[str] = None
    slug: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None
    created_at: datetime


