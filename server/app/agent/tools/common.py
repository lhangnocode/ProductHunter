from __future__ import annotations

from decimal import Decimal
from typing import Any

import app.models  # noqa: F401 – register all models before mapper config
from app.models.platform_product import PlatformProduct
from app.models.product import Product


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def platform_name(platform_product: PlatformProduct) -> str:
    platform = getattr(platform_product, "platform", None)
    return getattr(platform, "name", None) or f"Platform {platform_product.platform_id}"


def offer_payload(platform_product: PlatformProduct) -> dict[str, Any]:
    return {
        "platform_product_id": platform_product.id,
        "platform_id": platform_product.platform_id,
        "platform_name": platform_name(platform_product),
        "price": to_float(platform_product.current_price),
        "original_price": to_float(platform_product.original_price),
        "in_stock": bool(platform_product.in_stock),
        "url": platform_product.affiliate_url or platform_product.url,
        "last_crawled_at": (
            platform_product.last_crawled_at.isoformat()
            if platform_product.last_crawled_at
            else None
        ),
    }


def product_payload(product: Product, include_offers: bool = True) -> dict[str, Any]:
    offers = []
    if include_offers:
        offers = [
            offer_payload(platform_product)
            for platform_product in getattr(product, "platform_products", []) or []
        ]
        offers.sort(
            key=lambda offer: (
                not offer.get("in_stock", False),
                offer["price"] if offer["price"] is not None else float("inf"),
            )
        )
    in_stock_prices = [
        offer["price"]
        for offer in offers
        if offer.get("in_stock") and offer.get("price") is not None
    ]
    return {
        "product_id": product.id,
        "product_name": product.product_name or product.normalized_name,
        "normalized_name": product.normalized_name,
        "brand": product.brand,
        "category": product.category,
        "main_image_url": product.main_image_url,
        "lowest_price": min(in_stock_prices) if in_stock_prices else None,
        "offers": offers,
    }
