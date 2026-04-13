# app/models/user.py
import uuid
from sqlalchemy import Column, String, Text, SmallInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255))
    
    # 0 = FREE, 1 = PREMIUM
    plan = Column(SmallInteger, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    wish_lists = relationship("WishList", back_populates="user", cascade="all, delete-orphan")