from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class WishListCreate(BaseModel):
    product_id: UUID

class WishListItem(BaseModel):
    product_id: UUID
    added_at: datetime
    product_name: Optional[str] = None
    main_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class WishListResponse(BaseModel):
    items: List[WishListItem]