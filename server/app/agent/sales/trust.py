from __future__ import annotations

from typing import Any


def build_trust(
    product: dict[str, Any],
    offer: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a trust block from product/offer payload.

    Today's models do not carry `warranty_months`, `is_authentic`, or
    `return_days`. This function reads whatever is available and returns
    `None` for fields the data does not support.
    """
    warranty_months = None
    is_authentic = None
    return_days = None
    if offer is not None:
        warranty_months = _read_int(offer, "warranty_months")
        is_authentic = _read_bool(offer, "is_authentic")
        return_days = _read_int(offer, "return_days")
    if warranty_months is None:
        warranty_months = _read_int(product, "warranty_months")
    if is_authentic is None:
        is_authentic = _read_bool(product, "is_authentic")
    if return_days is None:
        return_days = _read_int(product, "return_days")

    return {
        "warranty_months": warranty_months,
        "is_authentic": is_authentic,
        "return_days": return_days,
    }


def trust_to_vietnamese(trust: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if trust.get("is_authentic") is True:
        lines.append("Hàng chính hãng.")
    elif trust.get("is_authentic") is False:
        lines.append("Lưu ý: cần xác minh nguồn gốc.")
    months = trust.get("warranty_months")
    if isinstance(months, int) and months > 0:
        lines.append(f"Bảo hành {months} tháng.")
    days = trust.get("return_days")
    if isinstance(days, int) and days > 0:
        lines.append(f"Đổi trả trong {days} ngày.")
    return lines


def _read_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_bool(payload: dict[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "chinh_hang", "chính hãng"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None
