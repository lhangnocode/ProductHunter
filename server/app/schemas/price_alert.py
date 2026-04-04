from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PriceAlertCreate(BaseModel):
    product_id: UUID
    target_price: float

class PriceAlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    target_price: float
    status: int
    created_at: datetime

    class Config:
        from_attributes = True