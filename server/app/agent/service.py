from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.events import AgentEventCallback, emit_event
from app.agent.langchain_orchestrator import run_langchain_agent, run_langchain_agent_stream
from app.agent.prompts import fallback_answer
from app.agent.schemas import AgentChatRequest, AgentChatResponse
from app.agent.tools.registry import build_langchain_tools

logger = logging.getLogger(__name__)


async def run_agent(
    request: AgentChatRequest,
    db: AsyncSession,
    event_callback: AgentEventCallback | None = None,
) -> AgentChatResponse:
    await emit_event(event_callback, "agent.started", {"message": request.message})
    tools = build_langchain_tools(db)

    answer = await run_langchain_agent(
        request=request,
        tools=tools,
    )

    if not answer:
        answer = fallback_answer([])

    response = AgentChatResponse(answer=answer)
    await emit_event(event_callback, "agent.done", response.model_dump(mode="json"))
    return response


async def run_agent_stream(
    request: AgentChatRequest,
    db: AsyncSession,
    event_callback: AgentEventCallback | None = None,
) -> AgentChatResponse:
    await emit_event(event_callback, "agent.started", {"message": request.message})
    tools = build_langchain_tools(db)

    answer_parts: list[str] = []

    async def handle_token(token: str) -> None:
        answer_parts.append(token)
        await emit_event(event_callback, "agent.token", {"content": token})

    logger.info("Starting LangChain agent streaming with %d tools", len(tools))
    answer = await run_langchain_agent_stream(
        request=request,
        tools=tools,
        on_tool_event=lambda name, data: emit_event(event_callback, name, data),
        on_token=handle_token,
    )

    if not answer:
        answer = "".join(answer_parts).strip() if answer_parts else fallback_answer([])

    response = AgentChatResponse(answer=answer)
    await emit_event(event_callback, "agent.done", response.model_dump(mode="json"))
    return response
