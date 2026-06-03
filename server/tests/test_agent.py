from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@patch("app.agent.service.run_langchain_agent", new_callable=AsyncMock)
async def test_agent_chat_returns_answer(
    mock_run_agent: AsyncMock,
    ac: AsyncClient,
):
    mock_run_agent.return_value = "Use the Shopee iPhone offer for this customer."

    response = await ac.post(
        "/api/v1/agent/chat",
        json={"message": "Can I sell this phone to a customer?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Use the Shopee iPhone offer for this customer."
    mock_run_agent.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.agent.service.run_langchain_agent_stream", new_callable=AsyncMock)
async def test_agent_chat_stream_emits_sse_events(
    mock_run_agent_stream: AsyncMock,
    ac: AsyncClient,
):
    mock_run_agent_stream.return_value = "Use this offer because it has current stock."

    response = await ac.post(
        "/api/v1/agent/chat/stream",
        json={"message": "Give me a telesales answer"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: agent.started" in body
    assert "event: agent.done" in body
