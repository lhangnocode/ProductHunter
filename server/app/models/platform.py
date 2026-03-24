import uuid 

from sqlalchemy import Column,  Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    base_url = Column(Text, nullable=False)
    affiliate_config = Column(Text, nullable=True)

    platform_products = relationship("PlatformProduct", back_populates="platform")