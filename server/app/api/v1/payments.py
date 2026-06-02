from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.payment_request import PaymentRequest

router = APIRouter()

# Thư mục lưu ảnh biên lai
UPLOAD_DIR = "static/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/request")
async def create_payment_request(
    amount: float = Form(...),
    receipt: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Xử lý lưu file ảnh
        file_extension = receipt.filename.split(".")[-1]
        new_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, new_filename)
        
        with open(file_path, "wb") as f:
            f.write(await receipt.read())

        # 2. Lưu thông tin vào Database
        # Lưu ý: Bạn cần import class PaymentRequest từ file models của bạn
        from sqlalchemy import insert
        from app.models.payment_request import PaymentRequest 
        
        new_payment = PaymentRequest(
            user_id=current_user.id,
            amount=amount,
            receipt_url=f"/static/receipts/{new_filename}",
            status=0 # 0 là Pending
        )
        
        db.add(new_payment)
        await db.commit()
        
        return {"status": "success", "message": "Yêu cầu của bạn đã được gửi tới Admin"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))