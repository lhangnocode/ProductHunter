from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TrendingDealCreate(BaseModel):
    product_id: UUID

class TrendingDealResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    main_image_url: Optional[str] = None
    current_price: float
    original_price: Optional[float] = None
    url: str
    deal_status: str
    deal_label: str
    platform_name: Optional[str] = None

    class Config:
        from_attributes = True