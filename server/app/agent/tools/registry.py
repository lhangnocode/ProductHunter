from __future__ import annotations

from uuid import UUID

from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.compare_prices import ComparePricesInput, compare_prices
from app.agent.tools.online_specs import OnlineSpecsInput, get_product_specs_online
from app.agent.tools.price_history import PriceHistoryInput, get_price_history
from app.agent.tools.product_detail import ProductDetailInput, get_product_detail
from app.agent.tools.search_products import SearchProductsInput, search_products


def build_langchain_tools(db: AsyncSession) -> list[StructuredTool]:
    async def _search_products(query: str, limit: int = 5) -> dict:
        return await search_products(db, query=query, limit=limit)

    async def _get_product_detail(product_id: UUID) -> dict:
        return await get_product_detail(db, product_id=product_id)

    async def _compare_prices(product_ids: list[UUID]) -> dict:
        return await compare_prices(db, product_ids=product_ids)

    async def _get_price_history(platform_product_ids: list[UUID]) -> dict:
        return await get_price_history(db, platform_product_ids=platform_product_ids)

    async def _get_product_specs_online(product_name: str) -> dict:
        return await get_product_specs_online(product_name=product_name)

    return [
        StructuredTool.from_function(
            coroutine=_search_products,
            name="search_products",
            description="Search ProductHunter products and current shop offers.",
            args_schema=SearchProductsInput,
        ),
        StructuredTool.from_function(
            coroutine=_get_product_detail,
            name="get_product_detail",
            description="Fetch product details and shop offers by product id.",
            args_schema=ProductDetailInput,
        ),
        StructuredTool.from_function(
            coroutine=_compare_prices,
            name="compare_prices",
            description="Compare current prices and stock across products.",
            args_schema=ComparePricesInput,
        ),
        StructuredTool.from_function(
            coroutine=_get_price_history,
            name="get_price_history",
            description="Summarize historical min and average prices for platform product ids.",
            args_schema=PriceHistoryInput,
        ),
        StructuredTool.from_function(
            coroutine=_get_product_specs_online,
            name="get_product_specs_online",
            description="Look up product specs online when local product data is missing.",
            args_schema=OnlineSpecsInput,
        ),
    ]
