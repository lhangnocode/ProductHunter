import asyncio
import logging
import os
from typing import Any, List, Optional, cast
from uuid import UUID

import typesense
from sqlalchemy import case, or_, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
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
                "query_by": "normalized_name,product_name",
                "query_by_weights": "2,8",
                "num_typos": 2,
                "min_len_1typo": 4,
                "min_len_2typo": 7,
                "typo_tokens_threshold": 1,
                "infix": "always",
                "drop_tokens_threshold": 1,
                "prefix": True,
                "enable_typos_for_numeric_tokens": "true",
                "prioritize_exact_match": "false",
                "split_join_tokens": "always",
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
                Product.product_name.ilike(f"%{query_value}%"),
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
    # 1. Subquery: Lấy Giá thấp nhất lịch sử
    subq_min = (
        select(
            PriceRecord.platform_product_id,
            func.min(PriceRecord.price).label("min_price")
        )
        .group_by(PriceRecord.platform_product_id)
        .subquery()
    )

    # 2. Subquery: Lấy Giá trung bình 30 ngày qua (Dùng func.now() của DB để tránh lệch múi giờ)
    thirty_days_interval = timedelta(days=30)
    subq_avg = (
        select(
            PriceRecord.platform_product_id,
            func.avg(PriceRecord.price).label("avg_price")
        )
        # Sửa lại cách lấy thời gian chuẩn xác trong SQL
        .where(PriceRecord.recorded_at >= (func.now() - thirty_days_interval))
        .group_by(PriceRecord.platform_product_id)
        .subquery()
    )

    # 3. Tạo câu truy vấn chính
    stmt = (
        select(PlatformProduct, subq_min.c.min_price, subq_avg.c.avg_price)
        .join(Product, PlatformProduct.product_id == Product.id) # Join lấy info product chính
        .outerjoin(subq_min, PlatformProduct.id == subq_min.c.platform_product_id)
        .outerjoin(subq_avg, PlatformProduct.id == subq_avg.c.platform_product_id)
        .options(
            selectinload(PlatformProduct.platform),
            joinedload(PlatformProduct.product) # Load thông tin cha (Product)
        )
    )

    # 4. Điều kiện LỌC (Rõ ràng và không dùng case)
    # Lấy sản phẩm nếu:
    # (Có min_price VÀ current_price <= min_price) HOẶC 
    # (Có avg_price VÀ current_price < avg_price)
    stmt = stmt.where(
        or_(
            and_(
                subq_min.c.min_price.is_not(None), 
                PlatformProduct.current_price <= subq_min.c.min_price
            ),
            and_(
                subq_avg.c.avg_price.is_not(None), 
                PlatformProduct.current_price < subq_avg.c.avg_price
            )
        )
    ).limit(limit)

    # 5. Thực thi truy vấn
    result = await db.execute(stmt)
    rows = result.all()

    trending_items = []
    
    # 6. Xử lý phân loại (Tagging) và Gói data trả về
    for row in rows:
        pp = row[0]
        min_p_val = row[1]
        avg_p_val = row[2]

        # --- XỬ LÝ LỖI ẢNH (QUAN TRỌNG) ---
        # Nếu link ảnh chứa srcset (có dấu phẩy), chỉ lấy link đầu tiên
        raw_img = pp.product.main_image_url if pp.product and pp.product.main_image_url else ""
        if "," in raw_img:
            # Tách lấy phần đầu tiên, sau đó tách khoảng trắng bỏ "1x"
            clean_img = raw_img.split(',')[0].split(' ')[0].strip()
            pp.product.main_image_url = clean_img

        # --- PHÂN LOẠI TAG ---
        current_p = float(pp.current_price) if pp.current_price else 0
        min_p = float(min_p_val) if min_p_val else current_p
        avg_p = float(avg_p_val) if avg_p_val is not None else (current_p + 1)
        
        setattr(pp, "deal_status", "stable")
        setattr(pp, "deal_label", "Giá ổn định")

        if current_p <= min_p and current_p < avg_p:
            setattr(pp, "deal_status", "extreme")
            setattr(pp, "deal_label", "Rẻ kỷ lục")

        elif current_p < avg_p:
            setattr(pp, "deal_status", "good")
            setattr(pp, "deal_label", "Giá tốt")
        trending_items.append(pp)

    status_order = {"extreme": 0, "good": 1, "stable": 2}
    trending_items.sort(key=lambda x: status_order.get(getattr(x, "deal_status", "stable"), 2))

    return trending_items