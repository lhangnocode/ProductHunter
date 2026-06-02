from uuid import UUID
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.payment_request import PaymentRequest
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

# --- USER MANAGEMENT ---

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