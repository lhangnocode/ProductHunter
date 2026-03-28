from fastapi import APIRouter

from app.api.v1 import crawler
from app.api.v1 import products
from app.api.v1 import platforms

api_router = APIRouter()
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
