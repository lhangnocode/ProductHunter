from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_dev_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    if not settings.DEV_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DEV_API_KEY is not configured on the server",
        )
    if x_api_key != settings.DEV_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
