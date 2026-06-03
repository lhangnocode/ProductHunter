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
    assert response.headers.get("access-control-allow-private-network") == "true"


@pytest.mark.asyncio
async def test_private_network_header_emitted_on_preflight(ac: AsyncClient):
    response = await ac.options(
        "/api/v1/agent/chat/stream",
        headers={
            "Origin": "https://product-hunter-xi.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-private-network") == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


@pytest.mark.asyncio
async def test_private_network_header_emitted_on_actual_response(ac: AsyncClient):
    response = await ac.get(
        "/health",
        headers={"Origin": "https://product-hunter-xi.vercel.app"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-private-network") == "true"


@pytest.mark.asyncio
async def test_local_network_origin_allowed_by_regex(ac: AsyncClient):
    response = await ac.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://192.168.100.80:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in {
        "*",
        "http://192.168.100.80:3000",
    }
