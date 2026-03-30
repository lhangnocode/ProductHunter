import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class PlatformProduct(Base):
    __tablename__ = "platform_products"
    __table_args__ = (UniqueConstraint("platform_id", "original_item_id", name="uq_platform_item"),)

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False)
    raw_name = Column(Text, nullable=True)
    original_item_id = Column(String(255), nullable=True)
    url = Column(Text, nullable=False)
    affiliate_url = Column(Text, nullable=True)
    current_price = Column(Numeric(12, 2), nullable=True)
    original_price = Column(Numeric(12, 2), nullable=True)
    in_stock = Column(Boolean, nullable=False, default=True, server_default="true")
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", back_populates="platform_products")
    platform = relationship("Platform", back_populates="platform_products")