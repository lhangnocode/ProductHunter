from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import settings
from app.api.v1.advisor import advisor_chat
from app.schemas.advisor import AdvisorChatMessage, AdvisorChatRequest, AdvisorChatResponse
from app.services import advisor as advisor_service
from app.services.advisor import (
    AdvisorCircuitOpenError,
    AdvisorConfigurationError,
    AdvisorIntent,
    AdvisorProviderError,
    AdvisorRetrievalError,
    OfferContext,
    ProductContext,
    _compact_query,
    _context_for_prompt,
    _fallback_answer,
    _offer_matches_price,
    _parse_intent,
    _parse_price_range,
    _parse_price_token,
    _product_matches_intent,
    _products_by_ids,
    _recommendations,
    _sources,
    _to_float,
    answer_advisor_chat,
    build_advisor_context,
    call_qwen,
)
from tests.conftest import TestingSessionLocal


def test_advisor_intent_parses_brand_category_and_price_range():
    intent = _parse_intent("Recommend Samsung phones priced from 10 to 12 million VND")

    assert intent.brand == "Samsung"
    assert "mobile" in intent.category_keywords
    assert intent.min_price == 10000000.0
    assert intent.max_price == 12000000.0


def test_advisor_offer_price_filter_matches_requested_budget():
    intent = _parse_intent("đề xuất điện thoại Samsung giá từ 10-12 triệu")

    assert _offer_matches_price(
        OfferContext(
            platform="Test",
            price=11000000.0,
            original_price=None,
            url=None,
            in_stock=True,
            last_crawled_at=None,
        ),
        intent,
    )
    assert not _offer_matches_price(
        OfferContext(
            platform="Test",
            price=309000.0,
            original_price=None,
            url=None,
            in_stock=True,
            last_crawled_at=None,
        ),
        intent,
    )


def test_advisor_numeric_and_intent_helpers_cover_edge_cases():
    assert _to_float(None) is None
    assert _to_float(Decimal("12.50")) == 12.5
    assert _to_float("bad") is None
    assert _parse_price_token("12,5", "trieu") == 12_500_000
    assert _parse_price_token("500", "k") == 500_000
    assert _parse_price_range("under 10 million") == (None, 10_000_000)
    assert _parse_price_range("trên 500 nghìn") == (500_000, None)
    assert _compact_query("tôi cần mua điện thoại Samsung dưới 10 triệu") == "điện thoại Samsung 10 triệu"


def test_advisor_product_and_offer_match_filters():
    product = SimpleNamespace(
        normalized_name="iPhone 15",
        product_name="Apple iPhone 15",
        brand="Apple",
        category="phone",
    )
    apple_phone = AdvisorIntent("iphone", "Apple", ["phone"], None, None)
    samsung_phone = AdvisorIntent("samsung", "Samsung", ["phone"], None, None)
    apple_laptop = AdvisorIntent("apple", "Apple", ["laptop"], None, None)

    assert _product_matches_intent(product, apple_phone)
    assert not _product_matches_intent(product, samsung_phone)
    assert not _product_matches_intent(product, apple_laptop)
    assert not _offer_matches_price(
        OfferContext("Shop", None, None, None, True, None),
        AdvisorIntent("phone", None, [], None, None),
    )


@pytest.mark.asyncio
async def test_advisor_products_by_ids_empty_returns_empty():
    async with TestingSessionLocal() as db:
        assert await _products_by_ids([], db) == []


@pytest.mark.asyncio
async def test_advisor_postgres_search_blank_query_returns_empty():
    async with TestingSessionLocal() as db:
        result = await advisor_service._postgres_product_search(
            AdvisorIntent(query=" ", brand=None, category_keywords=[], min_price=None, max_price=None),
            db=db,
            limit=5,
        )

    assert result == []


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
@patch("app.services.advisor.search_product", new_callable=AsyncMock)
@patch("app.services.advisor.call_qwen", new_callable=AsyncMock)
async def test_advisor_chat_falls_back_to_postgres_when_primary_search_fails(
    mock_call_qwen: AsyncMock,
    mock_search_product: AsyncMock,
    ac: AsyncClient,
    created_platform_product: dict,
):
    mock_search_product.side_effect = RuntimeError("primary search failed")
    mock_call_qwen.return_value = "iPhone recommendation from fallback search."

    response = await ac.post(
        "/api/v1/advisor/chat",
        json={"message": "đề xuất cho tôi iphone có giá tốt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "iPhone recommendation from fallback search."
    assert data["recommendations"][0]["product_id"] == created_platform_product["product_id"]


@pytest.mark.asyncio
@patch("app.services.advisor._postgres_product_search", new_callable=AsyncMock)
@patch("app.services.advisor.search_product", new_callable=AsyncMock)
@patch("app.services.advisor.call_qwen", new_callable=AsyncMock)
async def test_advisor_chat_returns_no_data_fallback_when_all_retrieval_fails(
    mock_call_qwen: AsyncMock,
    mock_search_product: AsyncMock,
    mock_postgres_product_search: AsyncMock,
    ac: AsyncClient,
):
    mock_search_product.side_effect = RuntimeError("primary search failed")
    mock_postgres_product_search.side_effect = RuntimeError("fallback search failed")

    response = await ac.post(
        "/api/v1/advisor/chat",
        json={"message": "đề xuất cho tôi điện thoại samsung có giá từ 10-12 triệu"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "could not find matching products" in data["answer"]
    assert data["recommendations"] == []
    mock_call_qwen.assert_not_awaited()


@pytest.mark.asyncio
async def test_advisor_chat_missing_qwen_key_returns_fallback_recommendation(
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

    assert response.status_code == 200
    data = response.json()
    assert "Based on ProductHunter data" in data["answer"]
    assert data["recommendations"][0]["product_id"] == created_platform_product["product_id"]


@pytest.mark.asyncio
async def test_advisor_chat_rejects_empty_message(ac: AsyncClient):
    response = await ac.post("/api/v1/advisor/chat", json={"message": ""})

    assert response.status_code == 422


def _advisor_product_with_offers():
    product_id = uuid.uuid4()
    first_offer_id = uuid.uuid4()
    second_offer_id = uuid.uuid4()
    product = SimpleNamespace(
        id=product_id,
        normalized_name="iphone 15",
        product_name="Apple iPhone 15",
        brand="Apple",
        category="phone",
        platform_products=[
            SimpleNamespace(
                id=first_offer_id,
                platform=SimpleNamespace(name="Shopee"),
                platform_id=1,
                current_price=Decimal("900"),
                original_price=Decimal("1000"),
                affiliate_url="https://aff.example/iphone",
                url="https://shop.example/iphone",
                in_stock=True,
                last_crawled_at=None,
            ),
            SimpleNamespace(
                id=second_offer_id,
                platform=None,
                platform_id=2,
                current_price=Decimal("1200"),
                original_price=None,
                affiliate_url=None,
                url="https://platform2.example/iphone",
                in_stock=False,
                last_crawled_at=None,
            ),
        ],
    )
    return product, first_offer_id, second_offer_id


@pytest.mark.asyncio
async def test_build_advisor_context_sorts_offers_and_enriches_price_history(monkeypatch):
    product, first_offer_id, second_offer_id = _advisor_product_with_offers()
    monkeypatch.setattr(advisor_service, "_retrieve_products", AsyncMock(return_value=[product]))
    monkeypatch.setattr(
        advisor_service,
        "_price_history_summary",
        AsyncMock(
            return_value={
                first_offer_id: {"min": Decimal("800"), "avg": Decimal("950")},
                second_offer_id: {"min": Decimal("1100"), "avg": Decimal("1300")},
            }
        ),
    )

    async with TestingSessionLocal() as db:
        contexts = await build_advisor_context(
            AdvisorChatRequest(message="recommend iphone"),
            db,
        )

    assert len(contexts) == 1
    assert contexts[0].lowest_price == 900.0
    assert contexts[0].price_history_min == 800.0
    assert contexts[0].price_history_avg == 1125.0
    assert contexts[0].offers[0].platform == "Shopee"
    assert contexts[0].offers[1].platform == "Platform 2"


@pytest.mark.asyncio
async def test_build_advisor_context_filters_out_budget_mismatches(monkeypatch):
    product, *_ = _advisor_product_with_offers()
    monkeypatch.setattr(advisor_service, "_retrieve_products", AsyncMock(return_value=[product]))
    monkeypatch.setattr(advisor_service, "_price_history_summary", AsyncMock(return_value={}))

    async with TestingSessionLocal() as db:
        contexts = await build_advisor_context(
            AdvisorChatRequest(message="recommend iphone under 100"),
            db,
        )

    assert contexts == []


@pytest.mark.asyncio
async def test_build_advisor_context_continues_when_price_history_fails(monkeypatch):
    product, *_ = _advisor_product_with_offers()
    monkeypatch.setattr(advisor_service, "_retrieve_products", AsyncMock(return_value=[product]))
    monkeypatch.setattr(
        advisor_service,
        "_price_history_summary",
        AsyncMock(side_effect=RuntimeError("history unavailable")),
    )

    async with TestingSessionLocal() as db:
        contexts = await build_advisor_context(
            AdvisorChatRequest(message="recommend iphone"),
            db,
        )

    assert len(contexts) == 1
    assert contexts[0].price_history_min is None


def test_advisor_prompt_fallback_recommendations_and_sources():
    product_id = uuid.uuid4()
    contexts = [
        ProductContext(
            id=product_id,
            name="Apple iPhone 15",
            normalized_name="iphone 15",
            brand="Apple",
            category="phone",
            lowest_price=900.0,
            price_history_min=800.0,
            price_history_avg=950.0,
            offers=[OfferContext("Shopee", 900.0, 1000.0, "https://shop.example", True, None)],
        )
    ]

    prompt = _context_for_prompt(contexts)
    fallback = _fallback_answer(AdvisorChatRequest(message="recommend iphone"), contexts)
    recommendations = _recommendations(contexts)
    sources = _sources(contexts)

    assert str(product_id) in prompt
    assert "lowest in-stock price" in fallback
    assert recommendations[0].reason == "Lowest in-stock price found: 900 VND"
    assert recommendations[0].platforms[0].platform == "Shopee"
    assert sources[0].id == str(product_id)


@pytest.mark.asyncio
async def test_call_qwen_builds_payload_and_includes_history(monkeypatch):
    captured = {}

    async def _fake_call_qwen_with_resilience(**kwargs):
        captured.update(kwargs)
        return "qwen answer"

    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(settings, "QWEN_BASE_URL", "https://qwen.example.test/")
    monkeypatch.setattr(advisor_service, "call_qwen_with_resilience", _fake_call_qwen_with_resilience)

    result = await call_qwen(
        AdvisorChatRequest(
            message="Which one?",
            history=[AdvisorChatMessage(role="user", content="Previous question")],
        ),
        [
            ProductContext(
                id=uuid.uuid4(),
                name="Apple iPhone 15",
                normalized_name="iphone 15",
                brand="Apple",
                category="phone",
                lowest_price=None,
                price_history_min=None,
                price_history_avg=None,
                offers=[],
            )
        ],
    )

    assert result == "qwen answer"
    assert captured["url"] == "https://qwen.example.test/chat/completions"
    assert captured["api_key"] == "test-key"
    assert captured["payload"]["messages"][-2]["content"] == "Previous question"
    assert captured["payload"]["messages"][-1]["content"] == "Which one?"


@pytest.mark.asyncio
async def test_answer_advisor_chat_falls_back_for_circuit_and_provider_errors(monkeypatch):
    contexts = [
        ProductContext(
            id=uuid.uuid4(),
            name="Apple iPhone 15",
            normalized_name="iphone 15",
            brand="Apple",
            category="phone",
            lowest_price=900.0,
            price_history_min=None,
            price_history_avg=None,
            offers=[OfferContext("Shopee", 900.0, None, "https://shop.example", True, None)],
        )
    ]
    monkeypatch.setattr(advisor_service, "build_advisor_context", AsyncMock(return_value=contexts))
    monkeypatch.setattr(advisor_service, "call_qwen", AsyncMock(side_effect=AdvisorCircuitOpenError("open")))

    async with TestingSessionLocal() as db:
        circuit_response = await answer_advisor_chat(AdvisorChatRequest(message="recommend"), db)

    monkeypatch.setattr(advisor_service, "call_qwen", AsyncMock(side_effect=AdvisorProviderError("failed")))
    async with TestingSessionLocal() as db:
        provider_response = await answer_advisor_chat(AdvisorChatRequest(message="recommend"), db)

    assert "Based on ProductHunter data" in circuit_response.answer
    assert "Based on ProductHunter data" in provider_response.answer


@pytest.mark.asyncio
async def test_advisor_chat_route_maps_service_errors(monkeypatch):
    request = AdvisorChatRequest(message="recommend")

    for error, expected_status in [
        (AdvisorConfigurationError("missing key"), 503),
        (AdvisorProviderError("provider failed"), 502),
        (AdvisorRetrievalError("retrieval failed"), 500),
        (RuntimeError("unexpected"), 500),
    ]:
        monkeypatch.setattr("app.api.v1.advisor.answer_advisor_chat", AsyncMock(side_effect=error))
        with pytest.raises(HTTPException) as exc_info:
            await advisor_chat(request, db=AsyncMock())
        assert exc_info.value.status_code == expected_status


@pytest.mark.asyncio
async def test_advisor_chat_route_success(monkeypatch):
    expected = AdvisorChatResponse(answer="ok", recommendations=[], sources=[])
    monkeypatch.setattr("app.api.v1.advisor.answer_advisor_chat", AsyncMock(return_value=expected))

    response = await advisor_chat(AdvisorChatRequest(message="recommend"), db=AsyncMock())

    assert response == expected
