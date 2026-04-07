import asyncio
import logging
import os
from typing import Any, List, Optional, cast
from uuid import UUID

import typesense
from sqlalchemy import case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.handlers.handler_product import (
    _build_typesense_client,
    _ensure_typesense_collection,
    _typesense_search,
)
from app.models.platform_product import PlatformProduct
from app.models.product import Product

logger = logging.getLogger(__name__)


async def search_platform_products(
    query: str,
    db: AsyncSession,
    limit: int = 20,
    page: int = 1,
    typesense_client: Optional[typesense.Client] = None,
) -> List[PlatformProduct]:
    if not query or not query.strip():
        return []

    query_value = query.strip()
    typesense_available = bool(typesense_client or settings.TYPESENSE_API_KEY or os.getenv("TYPESENSE_API_KEY"))

    if typesense_available:
        try:
            client = typesense_client or _build_typesense_client()
            await asyncio.to_thread(_ensure_typesense_collection, client)
            logger.info(
                "Platform product search using typesense; query=%s limit=%s page=%s",
                query_value,
                limit,
                page,
            )
            search_params: dict[str, Any] = {
                "q": query_value,
                "query_by": "normalized_name,slug",
                "query_by_weights": "8,2",
                "num_typos": 2,
                "min_len_1typo": 4,
                "min_len_2typo": 7,
                "typo_tokens_threshold": 1,
                "infix": "always",
                "drop_tokens_threshold": 2,
                "prefix": True,
                "per_page": limit,
                "page": page,
            }

            search_result = await asyncio.to_thread(
                _typesense_search,
                client,
                search_params,
            )
            hits = search_result.get("hits", [])

            product_ids: List[UUID] = []
            for hit in hits:
                doc = cast(dict[str, Any], hit.get("document", {}))
                raw_id = doc.get("id")
                if not isinstance(raw_id, str) or not raw_id:
                    continue
                try:
                    product_ids.append(UUID(cast(str, raw_id)))
                except ValueError:
                    continue

            if not product_ids:
                return []

            ordering = case(
                {product_id: index for index, product_id in enumerate(product_ids)},
                value=PlatformProduct.product_id,
            )

            stmt = (
                select(PlatformProduct)
                .options(
                    selectinload(PlatformProduct.platform),
                    selectinload(PlatformProduct.product),
                )
                .where(PlatformProduct.product_id.in_(product_ids))
                .order_by(ordering)
            )
            result = await db.execute(stmt)
            platform_products: List[PlatformProduct] = list(result.scalars().unique().all())
            return platform_products
        except Exception:
            logger.exception(
                "Typesense platform product search failed; falling back to postgres; query=%s limit=%s page=%s",
                query_value,
                limit,
                page,
            )

    logger.info(
        "Platform product search using postgres; query=%s limit=%s page=%s",
        query_value,
        limit,
        page,
    )
    product_stmt = (
        select(Product.id)
        .where(
            or_(
                Product.normalized_name.ilike(f"%{query_value}%"),
                Product.slug.ilike(f"%{query_value}%"),
            )
        )
        .offset((page - 1) * limit)
        .limit(limit)
    )
    product_result = await db.execute(product_stmt)
    product_ids = list(product_result.scalars().all())
    if not product_ids:
        return []

    ordering = case(
        {product_id: index for index, product_id in enumerate(product_ids)},
        value=PlatformProduct.product_id,
    )
    stmt = (
        select(PlatformProduct)
        .options(
            selectinload(PlatformProduct.platform),
            selectinload(PlatformProduct.product),
        )
        .where(PlatformProduct.product_id.in_(product_ids))
        .order_by(ordering)
    )
    result = await db.execute(stmt)
    platform_products: List[PlatformProduct] = list(result.scalars().unique().all())
    return platform_products


async def get_platform_products_by_product_id(
    product_id: UUID,
    db: AsyncSession,
    limit: int = 20,
    page: int = 1,
) -> List[PlatformProduct]:
    stmt = (
        select(PlatformProduct)
        .options(
            selectinload(PlatformProduct.platform),
            selectinload(PlatformProduct.product),
        )
        .where(PlatformProduct.product_id == product_id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    platform_products: List[PlatformProduct] = list(result.scalars().unique().all())
    return platform_products

