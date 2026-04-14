import asyncio
import logging
import os
from typing import Any, List, Optional, Tuple, cast
from uuid import UUID

import typesense
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from app.schemas.crawler import ProductIngestRequest


logger = logging.getLogger(__name__)

TYPESENSE_COLLECTION_SCHEMA: dict[str, Any] = {
    "name": "products",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "normalized_name", "type": "string", "infix": True},
        {"name": "product_name", "type": "string", "infix": True},
    ],
}
TYPESENSE_INFIX_FIELDS = ("normalized_name", "product_name")


def _typesense_search(client: typesense.Client, params: Any) -> Any:
    search_fn = cast(Any, client.collections["products"].documents.search)
    return search_fn(params)


def _ensure_typesense_collection(client: typesense.Client) -> None:
    collections = cast(Any, client.collections)
    collection_name = cast(str, TYPESENSE_COLLECTION_SCHEMA.get("name", "products"))
    try:
        existing = collections[collection_name].retrieve()
    except Exception as exc:
        object_not_found = getattr(getattr(typesense, "exceptions", None), "ObjectNotFound", None)
        error_code = getattr(exc, "code", None)
        if (object_not_found and isinstance(exc, object_not_found)) or error_code == 404:
            collections.create(TYPESENSE_COLLECTION_SCHEMA)
            logger.info("Created Typesense collection '%s'", collection_name)
            return
        raise

    existing_data = cast(dict[str, Any], existing)
    fields_raw = existing_data.get("fields", [])
    if isinstance(fields_raw, list):
        fields = {
            field.get("name"): field
            for field in fields_raw
            if isinstance(field, dict)
        }
        missing_infix = [
            field_name
            for field_name in TYPESENSE_INFIX_FIELDS
            if not fields.get(field_name, {}).get("infix")
        ]
        if missing_infix:
            logger.warning(
                "Typesense collection '%s' missing infix for fields=%s; recreate to enable infix search",
                collection_name,
                ",".join(missing_infix),
            )

def _build_typesense_client() -> typesense.Client:
    api_key = settings.TYPESENSE_API_KEY or os.getenv("TYPESENSE_API_KEY", "")
    if not api_key:
        raise RuntimeError("TYPESENSE_API_KEY is not configured")

    host = os.getenv("TYPESENSE_HOST")
    if not host:
        host = "typesense" if settings.POSTGRES_HOST == "postgres" else "localhost"
    port = int(os.getenv("TYPESENSE_PORT", "8108"))
    protocol = os.getenv("TYPESENSE_PROTOCOL", "http")

    return typesense.Client(
        {
            "nodes": [
                {
                    "host": host,
                    "port": port,
                    "protocol": protocol,
                }
            ],
            "api_key": api_key,
            "connection_timeout_seconds": 2,
        }
    )


async def upsert_product(
    payload: ProductIngestRequest,
    db: AsyncSession,
    typesense_client: Optional[typesense.Client] = None,
) -> Product:
    stmt = select(Product).where(Product.slug == payload.slug)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        product = Product(**payload.model_dump())
        db.add(product)
    else:
        for field, value in payload.model_dump().items():
            setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    client = typesense_client or _build_typesense_client()
    await asyncio.to_thread(_ensure_typesense_collection, client)
    document = {
        "id": str(product.id),
        "normalized_name": product.normalized_name,
        "product_name": product.product_name,
    }
    await asyncio.to_thread(
        client.collections["products"].documents.upsert,
        document,
    )
    return product


async def search_product(
    query: str,
    db: AsyncSession,
    limit: int = 20,
    page: int = 1,
    typesense_client: Optional[typesense.Client] = None,
) -> Tuple[List[Product], int]:
    if not query or not query.strip():
        return [], 0

    query_value = query.strip()
    typesense_available = bool(typesense_client or settings.TYPESENSE_API_KEY or os.getenv("TYPESENSE_API_KEY"))

    if typesense_available:
        try:
            client = typesense_client or _build_typesense_client()
            await asyncio.to_thread(_ensure_typesense_collection, client)
            logger.debug("Typesense is available, performing typesense search. query=%s, page=%s, limit=%s", query_value, page, limit)
            
            search_params: dict[str, Any] = {
                "q": query_value,
                "query_by": "normalized_name,product_name",
                "query_by_weights": "2,8",
                "num_typos": 1,
                "min_len_1typo": 5,
                "min_len_2typo": 9,
                "typo_tokens_threshold": 2,
                "infix": "off",
                "drop_tokens_threshold": 0,
                "prefix": True,
                "enable_typos_for_numeric_tokens": "false",
                "prioritize_exact_match": "true",
                "split_join_tokens": "off",
                "per_page": limit,
                "page": page,
            }

            search_result = await asyncio.to_thread(
                _typesense_search,
                client,
                search_params,
            )
            hits = search_result.get("hits", [])
            total_results = search_result.get("found", 0)
            logger.debug("Typesense search completed. found=%s, hits_count=%s", total_results, len(hits))

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
                return [], 0

            ordering = case(
                {product_id: index for index, product_id in enumerate(product_ids)},
                value=Product.id,
            )

            stmt = (
                select(Product)
                .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
                .where(Product.id.in_(product_ids))
                .order_by(ordering)
            )
            result = await db.execute(stmt)
            products: List[Product] = list(result.scalars().unique().all())
            
            return products, total_results 
            
        except Exception as exc:
            logger.exception("Typesense search failed; falling back to postgres... Exception: %s", exc)

    logger.info("Product search using postgres...")
    
    base_condition = or_(
        Product.normalized_name.ilike(f"%{query_value}%"),
        Product.product_name.ilike(f"%{query_value}%"),
    )
    
    count_stmt = select(func.count(Product.id)).where(base_condition)
    total_results = await db.scalar(count_stmt) or 0
    
    if total_results == 0:
        return [], 0

    stmt = (
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(base_condition)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    products: List[Product] = list(result.scalars().unique().all())

    return products, total_results
