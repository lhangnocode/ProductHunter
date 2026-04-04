import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"

    __table_args__ = {'extend_existing': True}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    brand = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    main_image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    platform_products = relationship("PlatformProduct", back_populates="product")
    price_alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")