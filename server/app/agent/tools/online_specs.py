from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OnlineSpecsInput(BaseModel):
    product_name: str = Field(..., min_length=1)


async def get_product_specs_online(product_name: str) -> dict[str, Any]:
    return {
        "product_name": product_name,
        "status": "not_configured",
        "specs": [],
        "message": "Online specs lookup is reserved for a later provider integration.",
    }
