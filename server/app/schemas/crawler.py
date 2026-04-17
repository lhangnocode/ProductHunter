from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductIngestRequest(BaseModel):
    normalized_name: str
    product_name: Optional[str] = None
    slug: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None


class ProductIngestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    normalized_name: str
    product_name: Optional[str] = None
    slug: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None
    created_at: datetime


class PlatformProductIngestRequest(BaseModel):
    product_id: Optional[UUID] = None
    platform_id: int
    raw_name: Optional[str] = None
    original_item_id: str
    url: str
    affiliate_url: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    rating: Optional[Decimal] = None # Cho phép null nếu chưa có đánh giá
    reviews_count: int = 0           # Mặc định là 0 lượt đánh giá
    in_stock: bool = True
    last_crawled_at: Optional[datetime] = None


class PlatformProductIngestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: Optional[UUID] = None
    platform_id: int
    raw_name: Optional[str] = None
    original_item_id: Optional[str] = None
    url: str
    affiliate_url: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    rating: Optional[Decimal] = None 
    reviews_count: int
    in_stock: bool
    last_crawled_at: Optional[datetime] = None
    deal_status: Optional[str] = None
