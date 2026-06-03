from __future__ import annotations

from typing import Any


_PHONE_KEYS = ("ram_gb", "battery_mah", "storage_gb", "refresh_rate_hz")
_PHONE_MIN_KEYS = 3
_LAPTOP_KEYS = ("ram_gb", "storage_gb", "cpu_score")
_LAPTOP_MIN_KEYS = 3


def _spec_density(
    specs: dict[str, Any],
    keys: tuple[str, ...],
    min_keys: int,
) -> float:
    total = 0.0
    counted = 0
    for key in keys:
        value = specs.get(key)
        if value is None:
            continue
        try:
            total += float(value)
            counted += 1
        except (TypeError, ValueError):
            continue
    if counted < min_keys:
        return 0.0
    return total / counted


def compute_value_score(
    product: dict[str, Any],
    specs: dict[str, Any] | None = None,
) -> float | None:
    """Return a value-for-money score, or None when not enough data.

    `product` is the agent product payload (lowest_price, category, etc.).
    `specs` is an optional free-form dict; today it is usually empty.
    """
    price = product.get("lowest_price")
    if price is None:
        return None
    try:
        price_value = float(price)
    except (TypeError, ValueError):
        return None
    if price_value <= 0:
        return None

    specs = specs or {}
    category = (product.get("category") or "").lower()
    if any(token in category for token in ("laptop", "macbook")):
        density = _spec_density(specs, _LAPTOP_KEYS, _LAPTOP_MIN_KEYS)
    else:
        density = _spec_density(specs, _PHONE_KEYS, _PHONE_MIN_KEYS)

    if density <= 0:
        return None

    raw = density / (price_value / 1_000_000.0)
    return round(min(100.0, max(0.0, raw)), 1)
