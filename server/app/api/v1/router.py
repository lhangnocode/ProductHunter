from fastapi import APIRouter

from app.api.v1 import crawler
from app.api.v1 import products
from app.api.v1 import platforms
from app.api.v1 import platform_products
from app.api.v1 import price_record
from app.api.v1 import price_alert
from app.api.v1 import auth

api_router = APIRouter()
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
api_router.include_router(platform_products.router, prefix="/platform_products", tags=["platform_product"])
api_router.include_router(price_record.router, prefix="/price_record", tags=["price_record"])
api_router.include_router(price_alert.router, prefix="/price_alerts", tags=["price_alerts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])