from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class WishListCreate(BaseModel):
    platform_product_id: Optional[UUID] = None
    product_id: Optional[UUID] = None

class WishListItem(BaseModel):
    product_id: UUID
    platform_product_id: UUID
    added_at: datetime
    product_name: Optional[str] = None
    main_image_url: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None

    class Config:
        from_attributes = True

class WishListResponse(BaseModel):
    items: List[WishListItem]
