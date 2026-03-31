from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PriceRecordResponse(BaseModel):
    id: int
    platform_product_id: UUID
    price: Decimal
    original_price: Optional[Decimal] = None
    is_flash_sale: bool
    recorded_at: datetime

    class Config:
        from_attributes = True # Cho phép Pydantic đọc dữ liệu từ SQLAlchemy Model
