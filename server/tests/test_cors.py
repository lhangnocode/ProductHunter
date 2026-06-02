import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_advisor_preflight_allows_vercel_origin(ac: AsyncClient):
    response = await ac.options(
        "/api/v1/advisor/chat",
        headers={
            "Origin": "https://product-hunter-xi.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in {
        "*",
        "https://product-hunter-xi.vercel.app",
    }
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
