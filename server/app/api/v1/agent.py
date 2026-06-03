from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.events import sse_event
from app.agent.schemas import AgentChatRequest, AgentChatResponse
from app.agent.service import run_agent
from app.db.session import get_db

router = APIRouter()


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentChatResponse:
    return await run_agent(request, db)


@router.post("/chat/stream")
async def agent_chat_stream(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    async def stream():
        queue: asyncio.Queue[tuple[str, dict] | None] = asyncio.Queue()

        async def collect(event: str, data: dict[str, Any]) -> None:
            await queue.put((event, data))

        async def execute_agent() -> None:
            try:
                await run_agent(request, db, event_callback=collect)
            finally:
                await queue.put(None)

        task = asyncio.create_task(execute_agent())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                event, data = item
                if event == "agent.done":
                    answer = str(data.get("answer") or "")
                    words = answer.split()
                    for index in range(0, len(words), 8):
                        yield sse_event(
                            "agent.token",
                            {"content": " ".join(words[index:index + 8])},
                        )
                    yield sse_event("agent.sources", {"sources": data.get("sources", [])})
                yield sse_event(event, data)
            await task
        except asyncio.CancelledError:
            task.cancel()
            raise

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
