from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@patch("app.agent.service.call_agent_model", new_callable=AsyncMock)
async def test_agent_chat_returns_product_recommendation(
    mock_call_agent_model: AsyncMock,
    ac: AsyncClient,
    created_platform_product: dict,
):
    mock_call_agent_model.return_value = "Use the Shopee iPhone offer for this customer."

    response = await ac.post(
        "/api/v1/agent/chat",
        json={
            "message": "Can I sell this phone to a customer?",
            "context": {"product_id": created_platform_product["product_id"]},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Use the Shopee iPhone offer for this customer."
    assert data["recommendations"][0]["product_id"] == created_platform_product["product_id"]
    assert data["recommendations"][0]["lowest_price"] == 28990000.0
    assert data["recommendations"][0]["offers"][0]["platform_name"] == "Shopee"
    assert data["sources"][0]["type"] == "product"
    assert [trace["tool_name"] for trace in data["tool_trace"]] == [
        "get_product_detail",
        "compare_prices",
        "get_price_history",
    ]
    mock_call_agent_model.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.agent.service.call_agent_model", new_callable=AsyncMock)
async def test_agent_chat_stream_emits_sse_events(
    mock_call_agent_model: AsyncMock,
    ac: AsyncClient,
    created_platform_product: dict,
):
    mock_call_agent_model.return_value = "Use this offer because it has current stock."

    response = await ac.post(
        "/api/v1/agent/chat/stream",
        json={
            "message": "Give me a telesales answer",
            "context": {"product_id": created_platform_product["product_id"]},
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: agent.started" in body
    assert "event: tool.started" in body
    assert "event: tool.finished" in body
    assert "event: agent.token" in body
    assert "event: agent.sources" in body
    assert "event: agent.done" in body
