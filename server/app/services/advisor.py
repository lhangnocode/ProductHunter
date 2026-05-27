import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.handlers.handler_product import search_product
from app.models.platform_product import PlatformProduct
from app.models.price_record import PriceRecord
from app.models.product import Product
from app.schemas.advisor import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorPlatformRecommendation,
    AdvisorRecommendation,
    AdvisorSource,
)

logger = logging.getLogger(__name__)


class AdvisorConfigurationError(RuntimeError):
    pass


class AdvisorProviderError(RuntimeError):
    pass


class AdvisorRetrievalError(RuntimeError):
    pass


@dataclass
class OfferContext:
    platform: str
    price: float | None
    original_price: float | None
    url: str | None
    in_stock: bool
    last_crawled_at: str | None


@dataclass
class ProductContext:
    id: UUID
    name: str
    normalized_name: str
    brand: str | None
    category: str | None
    lowest_price: float | None
    price_history_min: float | None
    price_history_avg: float | None
    offers: list[OfferContext]


@dataclass
class AdvisorIntent:
    query: str
    brand: str | None
    category_keywords: list[str]
    min_price: float | None
    max_price: float | None


BRAND_ALIASES = {
    "samsung": "Samsung",
    "apple": "Apple",
    "iphone": "Apple",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "poco": "Xiaomi",
    "oppo": "OPPO",
    "vivo": "Vivo",
    "realme": "Realme",
    "nokia": "Nokia",
    "nubia": "Nubia",
    "lenovo": "Lenovo",
    "asus": "Asus",
    "acer": "Acer",
    "dell": "Dell",
    "hp": "HP",
    "msi": "MSI",
    "prolink": "ProLink",
}

PHONE_KEYWORDS = ["phone", "phones", "mobile", "smartphone", "điện", "thoại", "dien", "thoai"]
CATEGORY_KEYWORD_MAP = {
    "phone": [
        "phone", "mobile", "smartphone", "điện thoại", "dien thoai",
        "galaxy", "iphone", "redmi", "poco", "oppo", "vivo", "realme",
    ],
}


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_query(message: str) -> str:
    words = re.findall(r"[\wÀ-ỹ]+", message, flags=re.UNICODE)
    stop_words = {
        "toi", "tôi", "can", "cần", "muon", "muốn", "mua", "nen", "nên",
        "chon", "chọn", "recommend", "recommendation", "advise", "advice",
        "under", "duoi", "dưới", "vnd", "dong", "đồng", "cho", "minh",
        "please", "product", "san", "sản", "pham", "phẩm", "de", "đề",
        "xuat", "xuất", "co", "có", "gia", "giá", "tu", "từ", "trong",
        "khoang", "khoảng",
    }
    useful = [word for word in words if word.lower() not in stop_words]
    return " ".join(useful[:8]) or message.strip()


def _parse_price_token(raw_value: str, unit: str | None) -> float:
    value = float(raw_value.replace(",", "."))
    unit_value = (unit or "").lower()
    if unit_value in {"tr", "triệu", "trieu", "million", "m"}:
        return value * 1_000_000
    if unit_value in {"k", "nghìn", "nghin", "thousand"}:
        return value * 1_000
    return value


def _parse_price_range(message: str) -> tuple[float | None, float | None]:
    normalized = message.lower()
    range_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:-|–|to|đến|den|tới|toi)\s*(\d+(?:[.,]\d+)?)\s*(tr|triệu|trieu|million|m|k|nghìn|nghin)?",
        normalized,
    )
    if range_match:
        unit = range_match.group(3)
        return (
            _parse_price_token(range_match.group(1), unit),
            _parse_price_token(range_match.group(2), unit),
        )

    under_match = re.search(
        r"(?:under|below|dưới|duoi|<=?)\s*(\d+(?:[.,]\d+)?)\s*(tr|triệu|trieu|million|m|k|nghìn|nghin)?",
        normalized,
    )
    if under_match:
        return None, _parse_price_token(under_match.group(1), under_match.group(2))

    over_match = re.search(
        r"(?:over|above|trên|tren|từ|tu|>=?)\s*(\d+(?:[.,]\d+)?)\s*(tr|triệu|trieu|million|m|k|nghìn|nghin)?",
        normalized,
    )
    if over_match:
        return _parse_price_token(over_match.group(1), over_match.group(2)), None

    return None, None


def _parse_intent(message: str, context_query: str | None = None) -> AdvisorIntent:
    combined = f"{message} {context_query or ''}".lower()
    brand = None
    for alias, canonical in BRAND_ALIASES.items():
        if re.search(rf"(^|[^\wÀ-ỹ]){re.escape(alias)}([^\wÀ-ỹ]|$)", combined, flags=re.UNICODE):
            brand = canonical
            break

    category_keywords: list[str] = []
    if any(keyword in combined for keyword in PHONE_KEYWORDS):
        category_keywords = CATEGORY_KEYWORD_MAP["phone"]

    min_price, max_price = _parse_price_range(combined)
    query = context_query.strip() if context_query and context_query.strip() else _compact_query(message)
    if brand and brand.lower() not in query.lower():
        query = f"{brand} {query}"
    return AdvisorIntent(
        query=query,
        brand=brand,
        category_keywords=category_keywords,
        min_price=min_price,
        max_price=max_price,
    )


async def _products_by_ids(product_ids: list[UUID], db: AsyncSession) -> list[Product]:
    if not product_ids:
        return []
    ordering = case(
        {product_id: index for index, product_id in enumerate(product_ids)},
        value=Product.id,
    )
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(Product.id.in_(product_ids))
        .order_by(ordering)
    )
    return list(result.scalars().unique().all())


async def _postgres_product_search(intent: AdvisorIntent, db: AsyncSession, limit: int) -> list[Product]:
    query_value = intent.query.strip()
    if not query_value:
        return []

    text_conditions = []

    if intent.brand:
        text_conditions.extend(
            [
                Product.brand.ilike(f"%{intent.brand}%"),
                Product.normalized_name.ilike(f"%{intent.brand}%"),
                Product.product_name.ilike(f"%{intent.brand}%"),
            ]
        )

    tokens = [token for token in re.findall(r"[\wÀ-ỹ]+", query_value, flags=re.UNICODE) if len(token) >= 2]
    for token in tokens[:6]:
        token_lower = token.lower()
        if token_lower in {
            "recommend", "priced", "price", "from", "million", "triệu", "trieu",
            "đề", "xuat", "xuất", "cho", "toi", "tôi", "vnd", "dong", "đồng",
        }:
            continue
        text_conditions.append(
            or_(
                Product.normalized_name.ilike(f"%{token}%"),
                Product.product_name.ilike(f"%{token}%"),
                Product.brand.ilike(f"%{token}%"),
                Product.category.ilike(f"%{token}%"),
            )
        )

    if intent.category_keywords:
        category_conditions = []
        for keyword in intent.category_keywords:
            category_conditions.extend(
                [
                    Product.normalized_name.ilike(f"%{keyword}%"),
                    Product.product_name.ilike(f"%{keyword}%"),
                    Product.category.ilike(f"%{keyword}%"),
                ]
            )
        text_conditions.append(or_(*category_conditions))

    if not text_conditions:
        text_conditions = [
            Product.normalized_name.ilike(f"%{query_value}%"),
            Product.product_name.ilike(f"%{query_value}%"),
        ]

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(or_(*text_conditions))
        .limit(max(limit * 8, 40))
    )
    return list(result.scalars().unique().all())


def _product_matches_intent(product: Product, intent: AdvisorIntent) -> bool:
    product_text = " ".join(
        str(value or "").lower()
        for value in [
            product.normalized_name,
            product.product_name,
            product.brand,
            product.category,
        ]
    )
    if intent.brand and intent.brand.lower() not in product_text:
        return False
    if intent.category_keywords and not any(keyword.lower() in product_text for keyword in intent.category_keywords):
        return False
    return True


def _offer_matches_price(offer: OfferContext, intent: AdvisorIntent) -> bool:
    if offer.price is None:
        return False
    if intent.min_price is not None and offer.price < intent.min_price:
        return False
    if intent.max_price is not None and offer.price > intent.max_price:
        return False
    return True


async def _retrieve_products(request: AdvisorChatRequest, db: AsyncSession) -> list[Product]:
    context = request.context
    context_query = context.search_query if context and context.search_query else None
    intent = _parse_intent(request.message, context_query)
    if context and context.product_id:
        try:
            products = await _products_by_ids([context.product_id], db)
            products = [product for product in products if _product_matches_intent(product, intent)]
            if products:
                return products
        except Exception:
            logger.exception("Advisor product lookup by id failed. product_id=%s", context.product_id)
            await db.rollback()

    products: list[Product] = []
    try:
        products, _ = await search_product(
            query=intent.query,
            db=db,
            limit=max(10, settings.ADVISOR_MAX_CONTEXT_PRODUCTS * 4),
            page=1,
        )
        products = [product for product in products if _product_matches_intent(product, intent)]
    except Exception as exc:
        logger.exception("Advisor primary product retrieval failed; trying postgres fallback. query=%s", intent.query)
        await db.rollback()

    if len(products) < settings.ADVISOR_MAX_CONTEXT_PRODUCTS:
        try:
            fallback_products = await _postgres_product_search(
                intent=intent,
                db=db,
                limit=max(1, settings.ADVISOR_MAX_CONTEXT_PRODUCTS),
            )
            seen_ids = {product.id for product in products}
            products.extend(
                product
                for product in fallback_products
                if product.id not in seen_ids and _product_matches_intent(product, intent)
            )
        except Exception:
            logger.exception("Advisor postgres fallback retrieval failed. query=%s", intent.query)
            await db.rollback()
    return products[: max(settings.ADVISOR_MAX_CONTEXT_PRODUCTS * 4, 20)]


async def _price_history_summary(platform_product_ids: list[UUID], db: AsyncSession) -> dict[UUID, dict[str, float | None]]:
    if not platform_product_ids:
        return {}

    result = await db.execute(
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price),
            func.avg(PriceRecord.price),
        )
        .where(PriceRecord.platform_product_id.in_(platform_product_ids))
        .group_by(PriceRecord.platform_product_id)
    )
    return {
        row[0]: {
            "min": _to_float(row[1]),
            "avg": _to_float(row[2]),
        }
        for row in result.all()
    }


async def build_advisor_context(request: AdvisorChatRequest, db: AsyncSession) -> list[ProductContext]:
    context_query = request.context.search_query if request.context and request.context.search_query else None
    intent = _parse_intent(request.message, context_query)
    products = await _retrieve_products(request, db)
    platform_product_ids = [
        platform_product.id
        for product in products
        for platform_product in getattr(product, "platform_products", []) or []
        if platform_product.id
    ]
    try:
        price_summaries = await _price_history_summary(platform_product_ids, db)
    except Exception:
        logger.exception("Advisor price history enrichment failed; continuing without price history")
        await db.rollback()
        price_summaries = {}

    contexts: list[ProductContext] = []
    for product in products:
        offers: list[OfferContext] = []
        product_history_mins: list[float] = []
        product_history_avgs: list[float] = []

        for platform_product in getattr(product, "platform_products", []) or []:
            price_summary = price_summaries.get(platform_product.id, {})
            if price_summary.get("min") is not None:
                product_history_mins.append(float(price_summary["min"]))
            if price_summary.get("avg") is not None:
                product_history_avgs.append(float(price_summary["avg"]))

            platform_name = (
                getattr(getattr(platform_product, "platform", None), "name", None)
                or f"Platform {platform_product.platform_id}"
            )
            offers.append(
                OfferContext(
                    platform=platform_name,
                    price=_to_float(platform_product.current_price),
                    original_price=_to_float(platform_product.original_price),
                    url=platform_product.affiliate_url or platform_product.url,
                    in_stock=bool(platform_product.in_stock),
                    last_crawled_at=(
                        platform_product.last_crawled_at.isoformat()
                        if platform_product.last_crawled_at
                        else None
                    ),
                )
            )

        if intent.min_price is not None or intent.max_price is not None:
            offers = [offer for offer in offers if _offer_matches_price(offer, intent)]

        offers.sort(
            key=lambda offer: (
                not offer.in_stock,
                offer.price if offer.price is not None else float("inf"),
            )
        )
        valid_offer_prices = [
            offer.price for offer in offers if offer.in_stock and offer.price is not None
        ]
        if (intent.min_price is not None or intent.max_price is not None) and not valid_offer_prices:
            continue

        product_name = product.product_name or product.normalized_name or str(product.id)
        contexts.append(
            ProductContext(
                id=product.id,
                name=product_name,
                normalized_name=product.normalized_name,
                brand=product.brand,
                category=product.category,
                lowest_price=min(valid_offer_prices) if valid_offer_prices else None,
                price_history_min=min(product_history_mins) if product_history_mins else None,
                price_history_avg=(
                    sum(product_history_avgs) / len(product_history_avgs)
                    if product_history_avgs
                    else None
                ),
                offers=offers[:3],
            )
        )

    contexts.sort(key=lambda product: product.lowest_price if product.lowest_price is not None else float("inf"))
    return contexts[: settings.ADVISOR_MAX_CONTEXT_PRODUCTS]


def _context_for_prompt(contexts: list[ProductContext]) -> str:
    if not contexts:
        return "No matching ProductHunter product data was found."

    payload = []
    for product in contexts:
        payload.append(
            {
                "product_id": str(product.id),
                "product_name": product.name,
                "normalized_name": product.normalized_name,
                "brand": product.brand,
                "category": product.category,
                "lowest_in_stock_price": product.lowest_price,
                "price_history_min": product.price_history_min,
                "price_history_avg": product.price_history_avg,
                "offers": [
                    {
                        "platform": offer.platform,
                        "price": offer.price,
                        "original_price": offer.original_price,
                        "in_stock": offer.in_stock,
                        "url": offer.url,
                        "last_crawled_at": offer.last_crawled_at,
                    }
                    for offer in product.offers
                ],
            }
        )
    return json.dumps(payload, ensure_ascii=False)


def _fallback_answer(request: AdvisorChatRequest, contexts: list[ProductContext]) -> str:
    if not contexts:
        return (
            "I could not find matching products in ProductHunter data for that request. "
            "Try adding a product type, brand, model, or budget so I can search more precisely."
        )

    lines = ["Based on ProductHunter data, these are the strongest options I found:"]
    for index, product in enumerate(contexts[:3], start=1):
        price = f"{product.lowest_price:,.0f} VND" if product.lowest_price is not None else "price unavailable"
        platform = product.offers[0].platform if product.offers else "available platforms"
        lines.append(f"{index}. {product.name}: lowest in-stock price is {price} on {platform}.")
    lines.append("Check the platform links and latest crawl time before buying because prices can change.")
    return "\n".join(lines)


async def call_qwen(request: AdvisorChatRequest, contexts: list[ProductContext]) -> str:
    if not settings.DASHSCOPE_API_KEY:
        raise AdvisorConfigurationError("DASHSCOPE_API_KEY is not configured")

    system_prompt = (
        "You are ProductHunter's shopping advisor. Use only the provided ProductHunter context "
        "for product facts, prices, stock, URLs, and price history. Prefer in-stock offers and "
        "explain tradeoffs briefly. If the context does not contain matching product data, say so "
        "and ask a specific narrowing question. Do not invent products, prices, stores, ratings, "
        "or discounts. Keep answers concise and practical."
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"ProductHunter context:\n{_context_for_prompt(contexts)}"},
    ]
    messages.extend(
        {"role": item.role, "content": item.content}
        for item in request.history[-6:]
    )
    messages.append({"role": "user", "content": request.message})

    payload = {
        "model": settings.QWEN_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 900,
    }
    url = settings.QWEN_BASE_URL.rstrip("/") + "/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=settings.QWEN_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.exception("Qwen advisor request failed")
        raise AdvisorProviderError("Qwen advisor request failed") from exc
    except ValueError as exc:
        logger.exception("Qwen advisor returned a non-JSON response")
        raise AdvisorProviderError("Qwen advisor returned a non-JSON response") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AdvisorProviderError("Qwen advisor returned an invalid response") from exc

    if not isinstance(content, str) or not content.strip():
        raise AdvisorProviderError("Qwen advisor returned an empty response")
    return content.strip()


def _recommendations(contexts: list[ProductContext]) -> list[AdvisorRecommendation]:
    recommendations: list[AdvisorRecommendation] = []
    for product in contexts:
        platforms = [
            AdvisorPlatformRecommendation(
                platform=offer.platform,
                price=offer.price,
                url=offer.url,
                in_stock=offer.in_stock,
            )
            for offer in product.offers
        ]
        reason = "Best matched ProductHunter result"
        if product.lowest_price is not None:
            reason = f"Lowest in-stock price found: {product.lowest_price:,.0f} VND"
        recommendations.append(
            AdvisorRecommendation(
                product_id=product.id,
                product_name=product.name,
                reason=reason,
                lowest_price=product.lowest_price,
                platforms=platforms,
            )
        )
    return recommendations


def _sources(contexts: list[ProductContext]) -> list[AdvisorSource]:
    return [
        AdvisorSource(type="product", id=str(product.id), label=product.name)
        for product in contexts
    ]


async def answer_advisor_chat(request: AdvisorChatRequest, db: AsyncSession) -> AdvisorChatResponse:
    contexts = await build_advisor_context(request, db)
    if contexts:
        try:
            answer = await call_qwen(request, contexts)
        except AdvisorConfigurationError:
            logger.warning("Qwen advisor key is not configured; returning deterministic advisor fallback")
            answer = _fallback_answer(request, contexts)
        except AdvisorProviderError:
            logger.exception("Qwen advisor failed; returning deterministic advisor fallback")
            answer = _fallback_answer(request, contexts)
    else:
        answer = _fallback_answer(request, contexts)

    return AdvisorChatResponse(
        answer=answer,
        recommendations=_recommendations(contexts),
        sources=_sources(contexts),
    )
