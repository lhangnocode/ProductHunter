import uuid
from sqlalchemy import Column, Numeric, SmallInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base  

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_product_id = Column(UUID(as_uuid=True), ForeignKey("platform_products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    target_price = Column(Numeric(12, 2), nullable=False)
    
    # 0 = ACTIVE, 1 = TRIGGERED
    status = Column(SmallInteger, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships để truy vấn ORM dễ dàng hơn
    user = relationship("User", back_populates="price_alerts")
    product = relationship("Product", back_populates="price_alerts")
    platform_product = relationship("PlatformProduct", back_populates="price_alerts")

    # Ràng buộc UNIQUE(user_id, platform_product_id) để theo dõi đúng offer trên từng sàn
    __table_args__ = (
        UniqueConstraint('user_id', 'platform_product_id', name='uq_user_platform_product_price_alert'),
    )
