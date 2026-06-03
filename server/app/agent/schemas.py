from __future__ import annotations

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


AgentChatRole = Literal["user", "assistant"]


class AgentChatMessage(BaseModel):
    role: AgentChatRole
    content: str = Field(..., min_length=1, max_length=4000)


class AgentChatContext(BaseModel):
    active_tab: Optional[str] = None
    search_query: Optional[str] = None
    product_id: Optional[UUID] = None
    shop_id: Optional[int] = None


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[AgentChatMessage] = Field(default_factory=list, max_length=20)
    context: Optional[AgentChatContext] = None
    include_tool_trace: bool = True


class AgentOffer(BaseModel):
    platform_product_id: UUID
    platform_id: int
    platform_name: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    in_stock: Optional[bool] = None
    url: Optional[str] = None
    last_crawled_at: Optional[str] = None
    deal_score: Optional[float] = None
    discount_pct: Optional[float] = None
    deal_reasons: list[str] = Field(default_factory=list)
    price_trend: Optional[str] = None


class AgentRecommendation(BaseModel):
    product_id: UUID
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    lowest_price: Optional[float] = None
    reason: str
    offers: list[AgentOffer] = Field(default_factory=list)
    deal_score: Optional[float] = None
    value_score: Optional[float] = None
    urgency_cues: list[str] = Field(default_factory=list)
    trust_warranty_months: Optional[int] = None
    trust_is_authentic: Optional[bool] = None
    trust_return_days: Optional[int] = None


class AgentAlternative(BaseModel):
    product_id: UUID
    product_name: str
    reason: str


class AgentObjectionAnswer(BaseModel):
    objection: str
    answer: str
    source_tool: str


class AgentSource(BaseModel):
    type: str
    id: str
    label: str


class AgentToolTrace(BaseModel):
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    status: Literal["success", "error"] = "success"
    error: Optional[str] = None


class AgentChatResponse(BaseModel):
    answer: str
    recommendations: list[AgentRecommendation] = Field(default_factory=list)
    sources: list[AgentSource] = Field(default_factory=list)
    tool_trace: list[AgentToolTrace] = Field(default_factory=list)
    handoff_required: bool = False
    alternatives: list[AgentAlternative] = Field(default_factory=list)
    objection_answers: list[AgentObjectionAnswer] = Field(default_factory=list)
    urgency_cues: list[str] = Field(default_factory=list)
    disclaimer: Optional[str] = None
