import asyncio
import logging
import os
from typing import Any, List, Optional, cast
from uuid import UUID

import typesense
from sqlalchemy import case, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.handlers.handler_product import (
    _build_typesense_client,
    _ensure_typesense_collection,
    _typesense_search,
)
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from app.models.price_record import PriceRecord

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


async def get_trending_deals(db: AsyncSession, limit: int = 20):
    # 1. Subquery lấy Giá thấp nhất lịch sử
    subq_min = (
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price).label("min_price")
        )
        .group_by(PriceRecord.platform_product_id)
        .subquery()
    )

    # 2. Subquery lấy Giá trung bình 30 ngày qua
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    subq_avg = (
        select(
            PriceRecord.platform_product_id,
            func.avg(PriceRecord.price).label("avg_price")
        )
        .where(PriceRecord.recorded_at >= thirty_days_ago)
        .group_by(PriceRecord.platform_product_id)
        .subquery()
    )

    # 3. Tạo biểu thức tính độ ưu tiên (Priority)
    # 1 = Extreme (Rẻ kỷ lục), 2 = Good (Giá tốt), 3 = Khác
    priority_expr = case(
        (PlatformProduct.current_price <= func.coalesce(subq_min.c.min_price, PlatformProduct.current_price), 1),
        (PlatformProduct.current_price < func.coalesce(subq_avg.c.avg_price, PlatformProduct.current_price), 2),
        else_=3
    )

    # 4. Truy vấn chính
    stmt = (
        select(PlatformProduct, priority_expr.label("deal_priority"))
        .outerjoin(subq_min, PlatformProduct.id == subq_min.c.platform_product_id)
        .outerjoin(subq_avg, PlatformProduct.id == subq_avg.c.platform_product_id)
        # Nạp trước (Eager load) bảng platform và bảng product (chứa original_name/image)
        .options(selectinload(PlatformProduct.platform))
        # CHỈ LẤY Extreme (1) HOẶC Good (2)
        .where(priority_expr <= 2)
        # Sắp xếp ưu tiên: Extreme trước, rồi mới tới Good. Sau đó xếp theo thời gian crawl mới nhất
        .order_by(priority_expr.asc(), PlatformProduct.last_crawled_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    
    # Do chúng ta select cả tuple (PlatformProduct, priority_expr), ta sẽ tách data ra
    trending_items = []
    for row in result.all():
        platform_product = row[0]
        # Nếu muốn, bạn có thể gán thêm cờ để trả về frontend báo hiệu đây là deal gì
        deal_type = "extreme" if row[1] == 1 else "good"
        setattr(platform_product, "deal_status", deal_type)
        trending_items.append(platform_product)

    return trending_items