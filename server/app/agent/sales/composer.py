from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agent.events import json_safe
from app.agent.sales.deal_score import compute_deal_score
from app.agent.sales.objections import build_objection_answers
from app.agent.sales.trust import build_trust
from app.agent.sales.urgency import build_urgency_cues
from app.agent.sales.value_score import compute_value_score
from app.agent.schemas import (
    AgentAlternative,
    AgentOffer,
    AgentObjectionAnswer,
    AgentRecommendation,
)


def _format_vnd(value: Any) -> str:
    if value is None:
        return "giá chưa cập nhật"
    try:
        return f"{float(value):,.0f}đ"
    except (TypeError, ValueError):
        return "giá chưa cập nhật"


def _best_offer(product: dict[str, Any]) -> dict[str, Any] | None:
    offers = product.get("offers") or []
    in_stock_offers = [o for o in offers if o.get("in_stock") and o.get("price") is not None]
    pool = in_stock_offers or [o for o in offers if o.get("price") is not None]
    if not pool:
        return None
    return min(pool, key=lambda item: float(item["price"]))


def _attach_deal_fields(
    offer_payload: dict[str, Any],
    history: dict[str, Any] | None,
) -> None:
    scored = compute_deal_score(offer_payload, history)
    offer_payload["deal_score"] = scored["deal_score"]
    offer_payload["discount_pct"] = scored["discount_pct"]
    offer_payload["deal_reasons"] = scored["deal_reasons"]
    if history and history.get("trend"):
        offer_payload["price_trend"] = history["trend"]


def compose_telesales_answer(
    products: list[dict[str, Any]],
    price_history_lookup: dict[str, dict[str, Any]] | None,
    message: str,
) -> dict[str, Any]:
    """Compose the sales-enriched agent answer payload.

    Returns a dict matching the sales fields of `AgentChatResponse`.
    """
    price_history_lookup = price_history_lookup or {}

    enriched_recos: list[AgentRecommendation] = []
    enriched_offers_payloads: list[dict[str, Any]] = []
    top_urgency: list[str] = []
    alternatives: list[AgentAlternative] = []

    for product in products:
        product_id = product.get("product_id")
        if product_id is None:
            continue
        product_id_str = str(product_id)

        best = _best_offer(product)
        history = price_history_lookup.get(product_id_str)
        if best is None:
            history = None
        else:
            best_platform_product_id = str(best.get("platform_product_id") or "")
            history = (
                price_history_lookup.get(best_platform_product_id)
                or price_history_lookup.get(product_id_str)
                or None
            )

        offer_payloads: list[dict[str, Any]] = []
        for raw_offer in product.get("offers") or []:
            offer_payload = dict(raw_offer)
            offer_history = price_history_lookup.get(str(offer_payload.get("platform_product_id") or ""))
            _attach_deal_fields(offer_payload, offer_history)
            offer_payloads.append(offer_payload)
            enriched_offers_payloads.append(offer_payload)

        first_offer = best or (offer_payloads[0] if offer_payloads else None)

        value_score = compute_value_score(product)
        urgency_cues = build_urgency_cues(first_offer or {}, history) if first_offer else []
        trust = build_trust(product, first_offer)

        if not top_urgency and urgency_cues:
            top_urgency = list(urgency_cues[:2])

        product_name = (
            product.get("product_name")
            or product.get("normalized_name")
            or product_id_str
        )

        reason = _build_reason(product, first_offer, value_score)
        offers_models = [
            AgentOffer.model_validate(json_safe(offer)) for offer in offer_payloads[:3]
        ]
        if first_offer is not None:
            best_model = next(
                (
                    offer
                    for offer in offers_models
                    if str(offer.platform_product_id) == str(first_offer.get("platform_product_id"))
                ),
                offers_models[0] if offers_models else None,
            )
            deal_score = best_model.deal_score if best_model else None
        else:
            deal_score = None

        enriched_recos.append(
            AgentRecommendation(
                product_id=product_id,
                product_name=str(product_name),
                brand=product.get("brand"),
                category=product.get("category"),
                lowest_price=product.get("lowest_price"),
                reason=reason,
                offers=offers_models,
                deal_score=deal_score,
                value_score=value_score,
                urgency_cues=urgency_cues,
                trust_warranty_months=trust.get("warranty_months"),
                trust_is_authentic=trust.get("is_authentic"),
                trust_return_days=trust.get("return_days"),
            )
        )

        for alt_raw in product.get("alternatives") or []:
            alt_id = alt_raw.get("product_id")
            if alt_id is None:
                continue
            alternatives.append(
                AgentAlternative(
                    product_id=alt_id,
                    product_name=str(alt_raw.get("product_name") or alt_id),
                    reason=str(alt_raw.get("reason") or "Sản phẩm cùng nhóm giá."),
                )
            )

    objection_dicts = build_objection_answers(message, products, price_history_lookup)
    objection_answers = [AgentObjectionAnswer.model_validate(item) for item in objection_dicts]

    disclaimer = _build_disclaimer(products, enriched_offers_payloads)

    return {
        "recommendations": enriched_recos,
        "alternatives": alternatives,
        "objection_answers": objection_answers,
        "urgency_cues": top_urgency,
        "disclaimer": disclaimer,
    }


def _build_reason(
    product: dict[str, Any],
    best_offer: dict[str, Any] | None,
    value_score: float | None,
) -> str:
    name = (
        product.get("product_name")
        or product.get("normalized_name")
        or "sản phẩm"
    )
    if best_offer is None:
        return f"Sản phẩm {name} phù hợp với yêu cầu."
    price_text = _format_vnd(best_offer.get("price"))
    platform = best_offer.get("platform_name") or "shop đang theo dõi"
    parts = [f"Giá tốt nhất hiện tại {price_text} tại {platform}."]
    if value_score is not None:
        parts.append(f"Điểm giá trị {value_score:.0f}/100.")
    return " ".join(parts)


def _build_disclaimer(
    products: list[dict[str, Any]],
    offers: list[dict[str, Any]],
) -> str | None:
    if not products or not offers:
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Giá và tồn kho cập nhật lúc {timestamp}. "
        "Anh chị xác nhận lại với shop trước khi chốt đơn."
    )
