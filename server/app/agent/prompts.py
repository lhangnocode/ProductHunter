from __future__ import annotations

import json

from app.agent.schemas import AgentChatRequest, AgentRecommendation, AgentSource


AGENT_SYSTEM_PROMPT = (
    "You are a telesales assistant for ProductHunter. Use only the supplied "
    "tool results for product, price, stock, and shop facts. Keep the answer "
    "short, practical, and ready for a telesales operator to say to a customer. "
    "If facts are missing, say what should be checked."
)


def build_agent_messages(
    request: AgentChatRequest,
    recommendations: list[AgentRecommendation],
    sources: list[AgentSource],
) -> list[dict[str, str]]:
    product_context = [
        recommendation.model_dump(mode="json")
        for recommendation in recommendations
    ]
    source_context = [source.model_dump(mode="json") for source in sources]

    messages: list[dict[str, str]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": json.dumps(
                {"products": product_context, "sources": source_context},
                ensure_ascii=False,
            ),
        },
    ]
    messages.extend(
        {"role": item.role, "content": item.content}
        for item in request.history[-8:]
    )
    messages.append({"role": "user", "content": request.message})
    return messages


def fallback_answer(
    recommendations: list[AgentRecommendation],
) -> str:
    if not recommendations:
        return (
            "I could not find a matching product in ProductHunter data. "
            "Ask the customer for a clearer product name, brand, category, or budget."
        )

    lines = ["Suggested telesales answer:"]
    for index, item in enumerate(recommendations[:3], start=1):
        price = f"{item.lowest_price:,.0f} VND" if item.lowest_price is not None else "price unavailable"
        offer = item.offers[0] if item.offers else None
        shop = offer.platform_name if offer else "available shops"
        lines.append(f"{index}. {item.product_name}: {price} at {shop}. {item.reason}")
    lines.append("Confirm current stock and price with the shop before closing the sale.")
    return "\n".join(lines)
