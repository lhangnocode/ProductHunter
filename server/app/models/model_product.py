import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    brand = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    main_image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    platform_products = relationship("PlatformProduct", back_populates="product")


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    base_url = Column(Text, nullable=False)
    affiliate_config = Column(Text, nullable=True)

    platform_products = relationship("PlatformProduct", back_populates="platform")


class PlatformProduct(Base):
    __tablename__ = "platform_products"
    __table_args__ = (UniqueConstraint("platform_id", "original_item_id", name="uq_platform_item"),)

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False)
    raw_name = Column(Text, nullable=True)
    original_item_id = Column(String(255), nullable=True)
    url = Column(Text, nullable=False)
    affiliate_url = Column(Text, nullable=True)
    current_price = Column(Numeric(12, 2), nullable=True)
    original_price = Column(Numeric(12, 2), nullable=True)
    in_stock = Column(Boolean, nullable=False, default=True, server_default="true")
    last_crawled_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="platform_products")
    platform = relationship("Platform", back_populates="platform_products")
