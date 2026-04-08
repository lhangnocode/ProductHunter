from typing import Optional 
from pydantic import BaseModel, Field


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

