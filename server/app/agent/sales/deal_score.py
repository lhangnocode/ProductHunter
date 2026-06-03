from __future__ import annotations

from typing import Any

PRICE_HISTORY_WINDOW_DAYS = 90
TREND_FALLING_THRESHOLD_PCT = 2.0
TREND_RISING_THRESHOLD_PCT = 2.0
LOW_STOCK_FRESH_HOURS = 24
DEAL_DISCOUNT_LIGHT = 5.0
DEAL_DISCOUNT_MID = 10.0
DEAL_DISCOUNT_STRONG = 20.0
DEAL_DISCOUNT_HUGE = 30.0


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_deal_score(
    offer: dict[str, Any],
    price_history: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a 0-100 deal score with Vietnamese reason lines.

    `offer` follows the shape produced by `tools.common.offer_payload`.
    `price_history` follows the shape produced by `tools.price_history`.
    Both are tolerant to missing fields.
    """
    reasons: list[str] = []
    score = 50.0

    current = _safe_float(offer.get("price"))
    original = _safe_float(offer.get("original_price"))

    if current is not None and original is not None and original > 0:
        discount_pct = max(0.0, (original - current) / original * 100.0)
        if discount_pct >= DEAL_DISCOUNT_HUGE:
            score += 30
            reasons.append(f"Đang giảm {discount_pct:.0f}% so với giá niêm yết.")
        elif discount_pct >= DEAL_DISCOUNT_STRONG:
            score += 20
            reasons.append(f"Đang giảm {discount_pct:.0f}% so với giá niêm yết.")
        elif discount_pct >= DEAL_DISCOUNT_MID:
            score += 12
            reasons.append(f"Giảm {discount_pct:.0f}% so với giá niêm yết.")
        elif discount_pct >= DEAL_DISCOUNT_LIGHT:
            score += 5
            reasons.append(f"Giảm nhẹ {discount_pct:.0f}%.")
    else:
        discount_pct = None

    in_stock = offer.get("in_stock")
    if in_stock is True:
        last = offer.get("last_crawled_at")
        score += 5
        if last:
            reasons.append("Còn hàng, dữ liệu cập nhật gần đây.")
        else:
            reasons.append("Còn hàng.")
    elif in_stock is False:
        score -= 25
        reasons.append("Tạm hết hàng.")

    if price_history:
        min_90d = _safe_float(price_history.get("min_90d"))
        avg_90d = _safe_float(price_history.get("avg_90d"))
        if current is not None and min_90d is not None and min_90d > 0:
            current_vs_min = (current - min_90d) / min_90d * 100.0
            if current_vs_min <= 2.0:
                score += 15
                reasons.append("Giá đang ở mức thấp nhất 90 ngày.")
            elif avg_90d is not None and avg_90d > 0 and current < avg_90d:
                gap = (avg_90d - current) / avg_90d * 100.0
                score += 7
                reasons.append(f"Thấp hơn trung bình 90 ngày khoảng {gap:.0f}%.")
        if price_history.get("trend") == "falling":
            score += 5
            reasons.append("Giá đang có xu hướng giảm.")
        elif price_history.get("trend") == "rising":
            score -= 5
            reasons.append("Giá đang có xu hướng tăng.")

    score = max(0.0, min(100.0, score))

    return {
        "deal_score": round(score, 1),
        "discount_pct": round(discount_pct, 1) if discount_pct is not None else None,
        "deal_reasons": reasons[:3],
    }
