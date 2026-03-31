from sqlalchemy import Column, BigInteger, Numeric, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(BigInteger, primary_key=True, index=True)
    
    platform_product_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("platform_products.id", ondelete="CASCADE"), 
        nullable=False,
        index=True # Về sau sẽ thêm trong db chính
    )

    # price DECIMAL(12,2) NOT NULL
    price = Column(Numeric(12, 2), nullable=False)
    
    # original_price DECIMAL(12,2)
    original_price = Column(Numeric(12, 2), nullable=True)
    
    # is_flash_sale BOOLEAN DEFAULT FALSE
    is_flash_sale = Column(Boolean, default=False)

    # recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())