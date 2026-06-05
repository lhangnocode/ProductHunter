from fastapi import APIRouter

from app.api.v1 import crawler
from app.api.v1 import products
from app.api.v1 import platforms
from app.api.v1 import platform_products
from app.api.v1 import price_record
from app.api.v1 import price_alert
from app.api.v1 import auth
from app.api.v1 import social_auth
from app.api.v1 import wish_list
from app.api.v1 import advisor
from app.api.v1 import agent
from app.api.v1 import payments
from app.api.v1 import admin
from app.api.v1 import device_tokens

api_router = APIRouter()
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
api_router.include_router(platform_products.router, prefix="/platform_products", tags=["platform_product"])
api_router.include_router(price_record.router, prefix="/price_record", tags=["price_record"])
api_router.include_router(price_alert.router, prefix="/price_alerts", tags=["price_alerts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(social_auth.router, prefix="/auth", tags=["social_auth"])
api_router.include_router(wish_list.router, prefix="/wish_lists", tags=["wish_lists"])
api_router.include_router(advisor.router, prefix="/advisor", tags=["advisor"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])

api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(device_tokens.router, prefix="/device_tokens", tags=["device_tokens"])
