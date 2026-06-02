import uuid
from sqlalchemy import Column, Numeric, SmallInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base

class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    receipt_url = Column(Text)
    status = Column(SmallInteger, default=0) # 0: Pending, 1: Approved, 2: Rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())