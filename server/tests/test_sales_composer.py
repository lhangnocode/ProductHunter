import uuid

from app.agent.recommendations import (
    recommendations_from_products,
    sales_payload_from_products,
)
from app.agent.sales.composer import compose_telesales_answer
from app.agent.schemas import AgentChatRequest


def _product(price: float, original: float | None = None, platform: str = "CellphoneS") -> dict:
    pp_id = str(uuid.uuid4())
    return {
        "product_id": str(uuid.uuid4()),
        "product_name": "iPhone 15 Pro Max 256GB",
        "normalized_name": "iphone 15 pro max 256gb",
        "brand": "Apple",
        "category": "Điện thoại",
        "lowest_price": price,
        "offers": [
            {
                "platform_product_id": pp_id,
                "platform_id": 1,
                "platform_name": platform,
                "price": price,
                "original_price": original,
                "in_stock": True,
            }
        ],
    }


def test_compose_enriches_recommendation_with_sales_fields():
    product = _product(price=22_000_000, original=25_000_000)
    history = {product["offers"][0]["platform_product_id"]: {"min_90d": 22_000_000, "trend": "falling"}}
    payload = compose_telesales_answer([product], history, "Đắt quá")
    assert len(payload["recommendations"]) == 1
    rec = payload["recommendations"][0]
    assert rec.deal_score is not None and rec.deal_score > 50
    assert rec.lowest_price == 22_000_000
    assert any("thấp nhất" in cue for cue in rec.urgency_cues)


def test_compose_builds_objection_answers_for_expensive_message():
    product = _product(price=22_000_000, original=25_000_000)
    payload = compose_telesales_answer([product], {}, "Đắt quá quá")
    assert payload["objection_answers"]
    assert payload["objection_answers"][0].source_tool in {"search_products", "compare_prices"}


def test_compose_emits_disclaimer():
    product = _product(price=22_000_000, original=25_000_000)
    payload = compose_telesales_answer([product], {}, "tư vấn giúp tôi")
    assert payload["disclaimer"] is not None
    assert "UTC" in payload["disclaimer"]


def test_compose_handles_no_products():
    payload = compose_telesales_answer([], {}, "")
    assert payload["recommendations"] == []
    assert payload["objection_answers"] == []
    assert payload["disclaimer"] is None


def test_recommendations_from_products_backward_compatible_shape():
    product = _product(price=22_000_000, original=25_000_000)
    recos = recommendations_from_products([product])
    assert len(recos) == 1
    rec = recos[0]
    assert str(rec.product_id) == product["product_id"]
    assert rec.lowest_price == 22_000_000
    assert rec.offers[0].platform_name == "CellphoneS"


def test_sales_payload_exposes_top_level_keys():
    product = _product(price=10_000_000, original=12_000_000)
    payload = sales_payload_from_products([product], {}, "Bên khác rẻ hơn 500k")
    assert "alternatives" in payload
    assert "objection_answers" in payload
    assert "urgency_cues" in payload
    assert "disclaimer" in payload


def test_request_message_routed_to_objection_detection():
    request = AgentChatRequest(message="Có trả góp không anh?")
    product = _product(price=15_000_000)
    payload = compose_telesales_answer([product], {}, request.message)
    objections = [o.objection for o in payload["objection_answers"]]
    assert any("trả góp" in obj.lower() for obj in objections)
