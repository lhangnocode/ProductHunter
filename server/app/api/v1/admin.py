from uuid import UUID
from decimal import Decimal
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.payment_request import PaymentRequest
from app.models.platform import Platform
from app.models.platform_product import PlatformProduct
from app.models.product import Product
from app.schemas.user import UserResponse

router = APIRouter()

# --- SCHEMAS ---
class UserPlanUpdate(BaseModel):
    plan: int = Field(..., ge=0, le=1)

class PaymentRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    amount: float
    receipt_url: str
    status: int
    created_at: Any

    class Config:
        from_attributes = True


class AdminOverviewCounts(BaseModel):
    products: int
    platform_products: int
    platforms: int
    in_stock_offers: int
    users: int
    pending_payments: int


class AdminOverviewProduct(BaseModel):
    id: UUID
    product_name: Optional[str] = None
    normalized_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image_url: Optional[str] = None
    offer_count: int = 0


class AdminOverviewOffer(BaseModel):
    platform_product_id: UUID
    product_id: Optional[UUID] = None
    product_name: str
    platform_id: int
    platform_name: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    in_stock: bool
    url: str
    last_crawled_at: Any = None


class AdminOverviewResponse(BaseModel):
    counts: AdminOverviewCounts
    recent_products: list[AdminOverviewProduct] = Field(default_factory=list)
    sample_offers: list[AdminOverviewOffer] = Field(default_factory=list)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

# --- USER MANAGEMENT ---

@router.get("/overview", response_model=AdminOverviewResponse)
async def get_admin_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    product_count = await db.scalar(select(func.count(Product.id))) or 0
    platform_product_count = await db.scalar(select(func.count(PlatformProduct.id))) or 0
    platform_count = await db.scalar(select(func.count(Platform.id))) or 0
    in_stock_offer_count = (
        await db.scalar(
            select(func.count(PlatformProduct.id)).where(PlatformProduct.in_stock.is_(True))
        )
        or 0
    )
    user_count = await db.scalar(select(func.count(User.id))) or 0
    pending_payment_count = (
        await db.scalar(select(func.count(PaymentRequest.id)).where(PaymentRequest.status == 0))
        or 0
    )

    offer_count_subquery = (
        select(
            PlatformProduct.product_id.label("product_id"),
            func.count(PlatformProduct.id).label("offer_count"),
        )
        .where(PlatformProduct.product_id.is_not(None))
        .group_by(PlatformProduct.product_id)
        .subquery()
    )
    recent_products_result = await db.execute(
        select(Product, func.coalesce(offer_count_subquery.c.offer_count, 0))
        .outerjoin(offer_count_subquery, Product.id == offer_count_subquery.c.product_id)
        .order_by(Product.created_at.desc().nullslast(), Product.id.desc())
        .limit(6)
    )
    recent_products = [
        AdminOverviewProduct(
            id=product.id,
            product_name=product.product_name,
            normalized_name=product.normalized_name,
            brand=product.brand,
            category=product.category,
            main_image_url=product.main_image_url,
            offer_count=int(offer_count or 0),
        )
        for product, offer_count in recent_products_result.all()
    ]

    sample_offers_result = await db.execute(
        select(PlatformProduct, Product, Platform)
        .select_from(PlatformProduct)
        .join(Platform, PlatformProduct.platform_id == Platform.id)
        .outerjoin(Product, PlatformProduct.product_id == Product.id)
        .where(PlatformProduct.in_stock.is_(True))
        .order_by(
            PlatformProduct.last_crawled_at.desc().nullslast(),
            PlatformProduct.current_price.asc().nullslast(),
            PlatformProduct.id.desc(),
        )
        .limit(8)
    )
    sample_offers = []
    for platform_product, product, platform in sample_offers_result.all():
        product_name = (
            getattr(product, "product_name", None)
            or getattr(product, "normalized_name", None)
            or platform_product.raw_name
            or "Unknown product"
        )
        sample_offers.append(
            AdminOverviewOffer(
                platform_product_id=platform_product.id,
                product_id=platform_product.product_id,
                product_name=product_name,
                platform_id=platform_product.platform_id,
                platform_name=platform.name,
                price=_to_float(platform_product.current_price),
                original_price=_to_float(platform_product.original_price),
                in_stock=bool(platform_product.in_stock),
                url=platform_product.affiliate_url or platform_product.url,
                last_crawled_at=platform_product.last_crawled_at,
            )
        )

    return AdminOverviewResponse(
        counts=AdminOverviewCounts(
            products=int(product_count),
            platform_products=int(platform_product_count),
            platforms=int(platform_count),
            in_stock_offers=int(in_stock_offer_count),
            users=int(user_count),
            pending_payments=int(pending_payment_count),
        ),
        recent_products=recent_products,
        sample_offers=sample_offers,
    )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/users/{user_id}/plan", response_model=UserResponse)
async def update_user_plan(
    user_id: UUID,
    payload: UserPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan = payload.plan
    await db.commit()
    await db.refresh(user)
    return user

# --- PAYMENT / UPGRADE APPROVAL ---

@router.get("/payments", response_model=List[PaymentRequestResponse])
async def list_payments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    # Join với bảng User để lấy Email
    stmt = (
        select(PaymentRequest, User.email)
        .join(User, PaymentRequest.user_id == User.id)
        .order_by(PaymentRequest.status.asc(), PaymentRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    
    output = []
    for row in result.all():
        pay, email = row
        output.append({
            "id": pay.id,
            "user_id": pay.user_id,
            "email": email,
            "amount": pay.amount,
            "receipt_url": pay.receipt_url,
            "status": pay.status,
            "created_at": pay.created_at
        })
    return output

@router.post("/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    # 1. Tìm yêu cầu thanh toán
    stmt = select(PaymentRequest).where(PaymentRequest.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment or payment.status != 0:
        raise HTTPException(status_code=400, detail="Yêu cầu không hợp lệ hoặc đã được xử lý")

    # 2. Cập nhật trạng thái yêu cầu thành Approved (1)
    payment.status = 1
    
    # 3. Nâng cấp User lên Plan 1 (Premium)
    user_stmt = update(User).where(User.id == payment.user_id).values(plan=1)
    await db.execute(user_stmt)
    
    await db.commit()
    return {"status": "success", "message": "Đã phê duyệt và nâng cấp tài khoản"}

@router.post("/payments/{payment_id}/reject")
async def reject_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    stmt = select(PaymentRequest).where(PaymentRequest.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Yêu cầu không tồn tại")

    payment.status = 2  # 2 = Rejected
    await db.commit()
    return {"status": "success", "message": "Đã từ chối yêu cầu"}
