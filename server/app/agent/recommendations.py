from __future__ import annotations

from typing import Any

from app.agent.events import json_safe
from app.agent.sales.composer import compose_telesales_answer
from app.agent.schemas import (
    AgentOffer,
    AgentRecommendation,
    AgentSource,
)


def recommendations_from_products(
    products: list[dict[str, Any]],
    price_history_lookup: dict[str, dict[str, Any]] | None = None,
    message: str = "",
) -> list[AgentRecommendation]:
    """Build AgentRecommendation list, with sales enrichment when available.

    Backward-compatible: a plain call with `products` produces a list that
    matches the pre-sales shape. The sales fields (deal_score, value_score,
    urgency_cues, trust_*) are populated when `price_history_lookup` and/or
    `message` are supplied.
    """
    if not products:
        return []

    sales = compose_telesales_answer(products, price_history_lookup, message)
    return list(sales.get("recommendations") or _legacy_recommendations(products))


def sales_payload_from_products(
    products: list[dict[str, Any]],
    price_history_lookup: dict[str, dict[str, Any]] | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Return the full sales payload (alternatives, objection_answers, etc.)."""
    return compose_telesales_answer(products, price_history_lookup, message)


def sources_from_recommendations(
    recommendations: list[AgentRecommendation],
) -> list[AgentSource]:
    sources: list[AgentSource] = []
    for recommendation in recommendations:
        sources.append(
            AgentSource(
                type="product",
                id=str(recommendation.product_id),
                label=recommendation.product_name,
            )
        )
        for offer in recommendation.offers:
            sources.append(
                AgentSource(
                    type="platform_product",
                    id=str(offer.platform_product_id),
                    label=f"{recommendation.product_name} on {offer.platform_name}",
                )
            )
    return sources


def _legacy_recommendations(products: list[dict[str, Any]]) -> list[AgentRecommendation]:
    recommendations: list[AgentRecommendation] = []
    for product in products:
        offers = [
            AgentOffer.model_validate(json_safe(offer))
            for offer in product.get("offers", [])[:3]
            if offer.get("platform_product_id")
        ]
        lowest_price = product.get("lowest_price")
        reason = "Matched the customer's request from ProductHunter data."
        if lowest_price is not None:
            reason = f"Lowest in-stock price found: {lowest_price:,.0f} VND."
        recommendations.append(
            AgentRecommendation(
                product_id=product["product_id"],
                product_name=(
                    product.get("product_name")
                    or product.get("normalized_name")
                    or str(product["product_id"])
                ),
                brand=product.get("brand"),
                category=product.get("category"),
                lowest_price=lowest_price,
                reason=reason,
                offers=offers,
            )
        )
    return recommendations
