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
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from app.schemas.crawler import ProductIngestRequest


logger = logging.getLogger(__name__)

TYPESENSE_COLLECTION_SCHEMA: dict[str, Any] = {
    "name": "products",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "normalized_name", "type": "string", "infix": True},
        {"name": "slug", "type": "string", "infix": True},
    ],
}
TYPESENSE_INFIX_FIELDS = ("normalized_name", "slug")


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
        "slug": product.slug,
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
) -> List[Product]:
    if not query or not query.strip():
        return []

    query_value = query.strip()
    typesense_available = bool(typesense_client or settings.TYPESENSE_API_KEY or os.getenv("TYPESENSE_API_KEY"))

    if typesense_available:
        try:
            client = typesense_client or _build_typesense_client()
            await asyncio.to_thread(_ensure_typesense_collection, client)
            logger.info(
                "Product search using typesense; query=%s limit=%s page=%s",
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
            return products
        except Exception:
            logger.exception(
                "Typesense search failed; falling back to postgres; query=%s limit=%s page=%s",
                query_value,
                limit,
                page,
            )

    logger.info(
        "Product search using postgres; query=%s limit=%s page=%s",
        query_value,
        limit,
        page,
    )
    stmt = (
        select(Product)
        .options(selectinload(Product.platform_products).selectinload(PlatformProduct.platform))
        .where(
            or_(
                Product.normalized_name.ilike(f"%{query_value}%"),
                Product.slug.ilike(f"%{query_value}%"),
            )
        )
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    products: List[Product] = list(result.scalars().unique().all())
    return products