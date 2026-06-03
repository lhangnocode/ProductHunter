from __future__ import annotations

from app.agent.prompts import build_agent_messages
from app.agent.schemas import AgentChatRequest, AgentRecommendation, AgentSource
from app.core.config import settings
from app.services.qwen_client import call_qwen_with_resilience


async def call_agent_model(
    request: AgentChatRequest,
    recommendations: list[AgentRecommendation],
    sources: list[AgentSource],
) -> str | None:
    if not settings.DASHSCOPE_API_KEY:
        return None

    payload = {
        "messages": build_agent_messages(request, recommendations, sources),
        "temperature": 0.2,
        "max_tokens": 800,
    }
    url = settings.QWEN_BASE_URL.rstrip("/") + "/chat/completions"
    return await call_qwen_with_resilience(
        url=url,
        api_key=settings.DASHSCOPE_API_KEY,
        payload=payload,
        timeout=float(settings.QWEN_TIMEOUT_SECONDS),
        max_attempts=2,
    )
