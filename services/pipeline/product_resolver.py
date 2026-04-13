"""
Stage 3a — Dedup via Typesense → resolve product_id

For each normalized row in staging, search Typesense using the derived
normalized_name to find an existing product match.
If found (brand matches), reuse its product_id (is_new=False).
Otherwise mark as new (product_id=None, is_new=True) for the persister to insert.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from services.crawler.core.storage.typesense_handler import TypesenseHandler


@dataclass
class ResolvedProduct:
    raw_id: str
    platform_id: int
    normalized_name: str        # derived in llm_normalizer: "<brand> <model> <specs...>"
    slug: str                   # slugified normalized_name
    brand: Optional[str]
    product_type: Optional[str] # e.g. "smartphone", "laptop" — from LLM
    model: Optional[str]        # e.g. "Poco M7 Pro 5G" — from LLM
    specs: Optional[list[dict[str, Any]]]  # [{name, value}, ...] — from LLM
    category: Optional[str]     # alias of product_type (kept for server DB compat)
    main_image_url: Optional[str]
    raw_name: str
    original_item_id: str
    url: Optional[str]
    affiliate_url: Optional[str]
    current_price: Optional[Decimal]
    original_price: Optional[Decimal]
    in_stock: Optional[bool]
    last_crawled_at: Optional[str]
    product_id: Optional[str] = field(default=None)
    is_new: bool = field(default=True)


def _slugify(text: str) -> str:
    """Unicode NFKD → ASCII → lowercase → alphanum+dash."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = "".join(ch if ch.isalnum() else "-" for ch in text)
    text = "-".join(part for part in text.split("-") if part)
    return text


def _brands_match(brand_a: Optional[str], brand_b: Optional[str]) -> bool:
    """
    Case-insensitive brand comparison.
    If either side is unknown (null), do NOT block the match —
    we'd rather merge than create a spurious duplicate.
    """
    if not brand_a or not brand_b:
        return True
    return brand_a.strip().lower() == brand_b.strip().lower()


def resolve_products(
    staging_conn,
    typesense: TypesenseHandler,
) -> list[ResolvedProduct]:
    """
    Fetch all 'done' normalized rows, resolve each against Typesense,
    and return a list of ResolvedProduct ready for the persister.
    """
    with staging_conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                rc.id,
                rc.platform_id,
                np.normalized_name,
                np.brand,
                np.product_type,
                np.model,
                np.specs,
                np.category,
                rc.main_image_url,
                rc.raw_name,
                rc.original_item_id,
                rc.url,
                rc.affiliate_url,
                rc.current_price,
                rc.original_price,
                rc.in_stock,
                rc.last_crawled_at
            FROM staging.raw_crawl rc
            JOIN staging.normalized_products np ON np.raw_id = rc.id
            WHERE rc.llm_status = 'done'
            ORDER BY rc.ingested_at
            """
        )
        rows = cur.fetchall()

    if not rows:
        print("[resolver] No normalized rows to resolve.")
        return []

    print(f"[resolver] Resolving {len(rows)} normalized rows against Typesense...")

    resolved: list[ResolvedProduct] = []
    # Cache: normalized_name → product_id (None means new product, no existing match)
    cache: dict[str, Optional[str]] = {}
    matched = 0
    new_count = 0

    typesense_enabled = True
    try:
        typesense.ensure_collection()
    except Exception as exc:
        print(f"[resolver] Typesense unavailable: {exc}. All products treated as new.")
        typesense_enabled = False

    for row in rows:
        (
            raw_id, platform_id, normalized_name, brand,
            product_type, model, specs, category,
            main_image_url, raw_name, original_item_id, url, affiliate_url,
            current_price, original_price, in_stock, last_crawled_at,
        ) = row

        slug = _slugify(normalized_name)
        product_id: Optional[str] = None
        is_new = True

        if typesense_enabled and normalized_name:
            cache_key = normalized_name.lower()
            if cache_key in cache:
                product_id = cache[cache_key]
                is_new = product_id is None
            else:
                try:
                    result = typesense.search(
                        "products",
                        query=normalized_name,
                        num_typos=0,    # strict: avoid cross-brand false merges
                        per_page=1,
                    )
                    hits = result.get("hits") or []
                    if hits:
                        doc = hits[0].get("document") or {}
                        hit_brand = doc.get("brand")
                        if _brands_match(brand, hit_brand):
                            product_id = str(doc.get("id") or "")
                            is_new = False
                    cache[cache_key] = product_id
                except Exception as exc:
                    print(f"[resolver] Typesense search error: {exc}")
                    typesense_enabled = False

        if is_new:
            new_count += 1
        else:
            matched += 1

        resolved.append(ResolvedProduct(
            raw_id=str(raw_id),
            platform_id=int(platform_id),
            normalized_name=normalized_name,
            slug=slug,
            brand=brand,
            product_type=product_type,
            model=model,
            specs=specs if isinstance(specs, list) else (list(specs) if specs else None),
            category=category or product_type,  # fall back to product_type if category absent
            main_image_url=main_image_url,
            raw_name=raw_name,
            original_item_id=original_item_id,
            url=url,
            affiliate_url=affiliate_url,
            current_price=Decimal(str(current_price)) if current_price is not None else None,
            original_price=Decimal(str(original_price)) if original_price is not None else None,
            in_stock=in_stock,
            last_crawled_at=str(last_crawled_at) if last_crawled_at else None,
            product_id=product_id or None,
            is_new=is_new,
        ))

    print(f"[resolver] Done. {matched} matched existing products, {new_count} new.")
    return resolved
