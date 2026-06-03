from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _hours_since(value: str | None) -> float | None:
    parsed = _parse_iso(value)
    if parsed is None:
        return None
    delta = datetime.now(timezone.utc) - parsed
    return delta.total_seconds() / 3600.0


def _format_vnd(value: float) -> str:
    return f"{value:,.0f}đ"


def build_urgency_cues(
    offer: dict[str, Any],
    price_history: dict[str, Any] | None,
) -> list[str]:
    """Return Vietnamese closer cues, only when data supports them."""
    cues: list[str] = []

    in_stock = offer.get("in_stock")
    last = offer.get("last_crawled_at")
    age_hours = _hours_since(last)

    if in_stock is True and age_hours is not None and age_hours <= 24:
        if age_hours < 1:
            cues.append("Cập nhật trong vòng 1 giờ qua.")
        else:
            cues.append(f"Cập nhật cách đây khoảng {int(age_hours)} giờ.")

    if price_history:
        current = _safe_float(offer.get("price"))
        min_90d = _safe_float(price_history.get("min_90d"))
        if current is not None and min_90d is not None and min_90d > 0:
            gap_pct = (current - min_90d) / min_90d * 100.0
            if gap_pct <= 0.5:
                cues.append("Giá đang ở mức thấp nhất 90 ngày.")
        if price_history.get("trend") == "falling":
            cues.append("Giá đang có xu hướng giảm trong 90 ngày qua.")

    return cues


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_price_text(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return "giá chưa cập nhật"
    return _format_vnd(number)
