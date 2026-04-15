from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
class PriceAlertCreate(BaseModel):
    product_id: UUID
    target_price: float

class PriceAlertResponse(BaseModel):
    product_id: UUID
    target_price: float
    status: int
    product_name: Optional[str] = None
    main_image_url: Optional[str] = None

    class Config:
        from_attributes = True