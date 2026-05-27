from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
@patch("app.services.advisor.call_qwen", new_callable=AsyncMock)
async def test_advisor_chat_returns_grounded_recommendations(
    mock_call_qwen: AsyncMock,
    ac: AsyncClient,
    created_platform_product: dict,
):
    mock_call_qwen.return_value = "The iPhone option is the best match from ProductHunter data."

    response = await ac.post(
        "/api/v1/advisor/chat",
        json={
            "message": "Should I buy this phone?",
            "context": {"product_id": created_platform_product["product_id"]},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The iPhone option is the best match from ProductHunter data."
    assert data["recommendations"][0]["product_id"] == created_platform_product["product_id"]
    assert data["recommendations"][0]["lowest_price"] == 28990000.0
    assert data["recommendations"][0]["platforms"][0]["platform"] == "Shopee"
    assert data["sources"][0]["type"] == "product"
    mock_call_qwen.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.advisor.call_qwen", new_callable=AsyncMock)
async def test_advisor_chat_no_data_uses_fallback_without_qwen(
    mock_call_qwen: AsyncMock,
    ac: AsyncClient,
):
    response = await ac.post(
        "/api/v1/advisor/chat",
        json={"message": "Recommend a product that does not exist in this database"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "could not find matching products" in data["answer"]
    assert data["recommendations"] == []
    assert data["sources"] == []
    mock_call_qwen.assert_not_awaited()


@pytest.mark.asyncio
async def test_advisor_chat_missing_qwen_key_returns_controlled_error(
    monkeypatch: pytest.MonkeyPatch,
    ac: AsyncClient,
    created_platform_product: dict,
):
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "")

    response = await ac.post(
        "/api/v1/advisor/chat",
        json={
            "message": "Should I buy this phone?",
            "context": {"product_id": created_platform_product["product_id"]},
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "DASHSCOPE_API_KEY is not configured"


@pytest.mark.asyncio
async def test_advisor_chat_rejects_empty_message(ac: AsyncClient):
    response = await ac.post("/api/v1/advisor/chat", json={"message": ""})

    assert response.status_code == 422
