from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any
from uuid import UUID


AgentEventCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


def json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value


async def emit_event(
    callback: AgentEventCallback | None,
    event: str,
    data: dict[str, Any],
) -> None:
    if callback is not None:
        await callback(event, json_safe(data))


def sse_event(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(json_safe(data), ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"
