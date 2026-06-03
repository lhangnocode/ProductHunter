from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.events import AgentEventCallback, emit_event
from app.agent.model_client import call_agent_model
from app.agent.prompts import fallback_answer
from app.agent.recommendations import recommendations_from_products, sources_from_recommendations
from app.agent.schemas import AgentChatRequest, AgentChatResponse, AgentToolTrace
from app.agent.tool_runner import run_tool
from app.agent.tools.registry import build_langchain_tools


def _query_from_request(request: AgentChatRequest) -> str:
    if request.context and request.context.search_query:
        return request.context.search_query
    return request.message


async def run_agent(
    request: AgentChatRequest,
    db: AsyncSession,
    event_callback: AgentEventCallback | None = None,
) -> AgentChatResponse:
    await emit_event(event_callback, "agent.started", {"message": request.message})
    tools = build_langchain_tools(db)
    trace: list[AgentToolTrace] = []
    products: list[dict[str, Any]] = []

    if request.context and request.context.product_id:
        detail = await run_tool(
            tools,
            trace,
            event_callback,
            "get_product_detail",
            {"product_id": request.context.product_id},
        )
        if detail and detail.get("found") and detail.get("product"):
            products = [detail["product"]]
    else:
        search_result = await run_tool(
            tools,
            trace,
            event_callback,
            "search_products",
            {"query": _query_from_request(request), "limit": 5},
        )
        if search_result:
            products = list(search_result.get("products") or [])

    product_ids = [
        product["product_id"]
        for product in products[:3]
        if product.get("product_id")
    ]
    if product_ids:
        compare_result = await run_tool(
            tools,
            trace,
            event_callback,
            "compare_prices",
            {"product_ids": product_ids},
        )
        if compare_result and compare_result.get("products"):
            products = list(compare_result["products"])

    platform_product_ids = [
        offer["platform_product_id"]
        for product in products
        for offer in product.get("offers", [])[:2]
        if offer.get("platform_product_id")
    ]
    if platform_product_ids:
        await run_tool(
            tools,
            trace,
            event_callback,
            "get_price_history",
            {"platform_product_ids": platform_product_ids[:10]},
        )

    if not products:
        await run_tool(
            tools,
            trace,
            event_callback,
            "get_product_specs_online",
            {"product_name": _query_from_request(request)},
        )

    recommendations = recommendations_from_products(products[:5])
    sources = sources_from_recommendations(recommendations)

    try:
        answer = await call_agent_model(request, recommendations, sources)
    except Exception:
        answer = None
    if not answer:
        answer = fallback_answer(recommendations)

    response = AgentChatResponse(
        answer=answer,
        recommendations=recommendations,
        sources=sources,
        tool_trace=trace if request.include_tool_trace else [],
        handoff_required=not bool(recommendations),
    )
    await emit_event(event_callback, "agent.done", response.model_dump(mode="json"))
    return response
