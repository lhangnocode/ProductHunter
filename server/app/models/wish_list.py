from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class WishList(Base):
    __tablename__ = "wish_list"

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ràng buộc duy nhất: Một cặp (user_id, product_id) không được lặp lại
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_wishlist"),
    )

    product = relationship("Product", back_populates="wish_lists")
    user = relationship("User", back_populates="wish_lists")