from __future__ import annotations

import json
import logging
from typing import Awaitable, Callable

import httpx

from app.agent.prompts import build_agent_messages
from app.agent.schemas import AgentChatRequest, AgentRecommendation, AgentSource
from app.core.config import settings
from app.services.qwen_client import call_qwen_with_resilience

logger = logging.getLogger(__name__)

AgentTokenCallback = Callable[[str], Awaitable[None]]


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


async def call_agent_model_stream(
    request: AgentChatRequest,
    recommendations: list[AgentRecommendation],
    sources: list[AgentSource],
    on_token: AgentTokenCallback | None = None,
) -> str | None:
    if not settings.DASHSCOPE_API_KEY:
        return None

    payload = {
        "messages": build_agent_messages(request, recommendations, sources),
        "temperature": 0.2,
        "max_tokens": 800,
        "stream": True,
    }
    url = settings.QWEN_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    chunks: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=float(settings.QWEN_TIMEOUT_SECONDS)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    choice = (data.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if not content:
                        message = choice.get("message") or {}
                        content = message.get("content")
                    if not content:
                        continue
                    chunks.append(content)
                    if on_token is not None:
                        await on_token(content)
    except httpx.HTTPError as exc:
        logger.warning("Agent streaming failed, fallback to non-streaming: %s", exc)
        return None

    answer = "".join(chunks).strip()
    return answer or None
