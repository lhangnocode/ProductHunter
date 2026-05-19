"""
RawProduct — the single data model produced by every crawler.

This is a pure data container. No methods, no business logic, no DB knowledge.
Crawlers fill it; the pipeline reads it from CSV.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


@dataclass
class RawProduct:
    """
    Represents one product listing scraped from a single platform page.

    One RawProduct maps to one row in staging.raw_crawl and ultimately
    one row in platform_products (server DB).

    Fields
    ------
    platform_id : int
        Numeric ID of the source platform (e.g. 7 = FPT Shop, 8 = Phong Vũ).
        Matches the `id` column in the server DB `platforms` table.

    raw_name : str
        The exact product title as it appears on the platform page.
        Never cleaned or translated here — the pipeline LLM handles that.

    url : str
        Full absolute URL of the product listing page.
        Also serves as the natural unique key for a listing.

    price : Decimal | None
        Current selling price in VND. None if not shown or unparseable.

    original_price : Decimal | None
        Original / list price before any discount in VND. None if not shown.

    category : str | None
        The platform's own category slug (e.g. "may-tinh-xach-tay", "c/laptop").
        Optional — if absent, the pipeline LLM normalizer will infer it from
        the product name.

    main_image_url : str | None
        Absolute URL of the primary product image. None if not found.

    crawled_at : datetime
        UTC timestamp set at parse time. Always timezone-aware.
    """

    platform_id:    int
    raw_name:       str
    url:            str
    current_price:  Optional[Decimal]
    original_price: Optional[Decimal]
    category:       Optional[str]
    main_image_url: Optional[str]
    crawled_at:     datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ── Validation ────────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        if not self.raw_name or not self.raw_name.strip():
            raise ValueError("raw_name must not be empty")
        if not self.url or not self.url.strip():
            raise ValueError("url must not be empty")
        if self.platform_id <= 0:
            raise ValueError(f"platform_id must be a positive integer, got {self.platform_id!r}")
        if not self.crawled_at.tzinfo:
            raise ValueError("crawled_at must be timezone-aware (use datetime.now(timezone.utc))")

    # ── Serialization helpers (used by CSV writer) ────────────────────────────

    @classmethod
    def csv_headers(cls) -> list[str]:
        """Column names in the order written to CSV."""
        return [
            "platform_id",
            "raw_name",
            "url",
            "current_price",
            "original_price",
            "category",
            "main_image_url",
            "crawled_at",
        ]

    def to_csv_row(self) -> list[str]:
        """Serialise to a list of strings in the same order as csv_headers()."""
        return [
            str(self.platform_id),
            self.raw_name,
            self.url,
            str(self.current_price) if self.current_price is not None else "",
            str(self.original_price) if self.original_price is not None else "",
            self.category or "",
            self.main_image_url or "",
            self.crawled_at.isoformat(),
        ]

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "RawProduct":
        """
        Deserialise from a csv.DictReader row (all values are strings).
        Used by the pipeline's StagingLoader to read crawler output.
        """
        def _decimal(val: str) -> Optional[Decimal]:
            v = val.strip()
            return Decimal(v) if v else None

        def _optional_str(val: str) -> Optional[str]:
            v = val.strip()
            return v if v else None

        def _dt(val: str) -> datetime:
            dt = datetime.fromisoformat(val.strip())
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        return cls(
            platform_id=int(row["platform_id"]),
            raw_name=row["raw_name"],
            url=row["url"],
            current_price=_decimal(row.get("current_price", "")),
            original_price=_decimal(row.get("original_price", "")),
            category=_optional_str(row.get("category", "")),
            main_image_url=_optional_str(row.get("main_image_url", "")),
            crawled_at=_dt(row["crawled_at"]),
        )
