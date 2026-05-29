from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant"]


class AdvisorChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(..., min_length=1, max_length=4000)


class AdvisorChatContext(BaseModel):
    active_tab: Optional[str] = None
    search_query: Optional[str] = None
    product_id: Optional[UUID] = None


class AdvisorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[AdvisorChatMessage] = Field(default_factory=list, max_length=12)
    context: Optional[AdvisorChatContext] = None


class AdvisorPlatformRecommendation(BaseModel):
    platform: str
    price: Optional[float] = None
    url: Optional[str] = None
    in_stock: Optional[bool] = None


class AdvisorRecommendation(BaseModel):
    product_id: UUID
    product_name: str
    reason: str
    lowest_price: Optional[float] = None
    platforms: list[AdvisorPlatformRecommendation] = Field(default_factory=list)


class AdvisorSource(BaseModel):
    type: str
    id: str
    label: str


class AdvisorChatResponse(BaseModel):
    answer: str
    recommendations: list[AdvisorRecommendation] = Field(default_factory=list)
    sources: list[AdvisorSource] = Field(default_factory=list)
