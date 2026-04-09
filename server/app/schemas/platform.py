import datetime
from typing import Optional 
from pydantic import BaseModel, Field
from datetime import datetime


class PlatformCreateRequest(BaseModel):
    name: str = Field(..., example="Shopee")
    base_url: str
    affiliate_config: Optional[str] = None

class PlatformResponse(BaseModel):
    id: int
    name: str
    base_url: str
    affiliate_config: Optional[str] = None

    class Config:
        from_attributes = True


class PlatformPriceItem(BaseModel):
    platform_id: int
    url: str
    affiliate_url: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    in_stock: bool
    last_crawled_at: Optional[datetime] = None

