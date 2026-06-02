from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v1.platform_products import get_all_platform_products, get_trending_platform_products


@pytest.mark.asyncio
async def test_get_all_platform_products_maps_db_error_to_500():
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await get_all_platform_products(db=db)

    assert exc_info.value.status_code == 500
    assert "Lỗi khi truy vấn dữ liệu" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_trending_platform_products_maps_service_error_to_500(monkeypatch: pytest.MonkeyPatch):
    async def _raise(*args, **kwargs):
        raise RuntimeError("trending unavailable")

    monkeypatch.setattr("app.api.v1.platform_products.get_trending_deals", _raise)

    with pytest.raises(HTTPException) as exc_info:
        await get_trending_platform_products(db=AsyncMock(), limit=20)

    assert exc_info.value.status_code == 500
    assert "Lỗi khi lấy danh sách trending" in exc_info.value.detail
