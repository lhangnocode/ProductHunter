from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TrendingDealCreate(BaseModel):
    product_id: UUID

class TrendingDealResponse(BaseModel):
    id: UUID
    platform_product_id: UUID
    product_id: UUID
    product_name: str
    raw_name: Optional[str] = None
    main_image_url: Optional[str] = None
    current_price: float
    original_price: Optional[float] = None
    url: str
    deal_status: str
    deal_label: str
    platform_id: Optional[int] = None
    platform_name: Optional[str] = None
    in_stock: Optional[bool] = None
    rating: Optional[float] = None

    class Config:
        from_attributes = True
