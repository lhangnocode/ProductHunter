from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
class PriceAlertCreate(BaseModel):
    platform_product_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    target_price: float

class PriceAlertResponse(BaseModel):
    product_id: UUID
    platform_product_id: UUID
    target_price: float
    status: int
    product_name: Optional[str] = None
    main_image_url: Optional[str] = None
    current_price: Optional[float] = None

    class Config:
        from_attributes = True
