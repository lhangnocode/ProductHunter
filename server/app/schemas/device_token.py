from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceTokenCreate(BaseModel):
    token: str = Field(..., min_length=1)
    platform: str = Field(default="android", max_length=32)


class DeviceTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    token: str
    platform: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_seen_at: datetime | None = None
