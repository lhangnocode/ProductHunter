from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.wish_list import WishList
from app.schemas.wish_list import WishListItem, WishListResponse


async def _get_wishlist_rows(db: AsyncSession, user_id: UUID) -> List[WishList]:
	stmt = (
		select(WishList)
		.options(selectinload(WishList.product))
		.where(WishList.user_id == user_id)
		.order_by(WishList.added_at.desc())
	)
	result = await db.execute(stmt)
	return list(result.scalars().all())


def _to_response(rows: List[WishList]) -> WishListResponse:
	items = [
		WishListItem(
			product_id=row.product_id,
			added_at=row.added_at,
			product_name=row.product.normalized_name if row.product else None,
			main_image_url=row.product.main_image_url if row.product else None,
		)
		for row in rows
	]
	return WishListResponse(items=items)


async def add_to_wishlist(db: AsyncSession, user_id: UUID, product_id: UUID) -> WishListResponse:
	product_stmt = select(Product.id).where(Product.id == product_id)
	product_result = await db.execute(product_stmt)
	if product_result.scalar_one_or_none() is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Product not found",
		)

	stmt = (
		insert(WishList)
		.values(user_id=user_id, product_id=product_id)
		.on_conflict_do_nothing(index_elements=["user_id", "product_id"])
	)
	await db.execute(stmt)
	await db.commit()

	rows = await _get_wishlist_rows(db, user_id)
	return _to_response(rows)


async def get_user_wishlist(db: AsyncSession, user_id: UUID) -> WishListResponse:
	rows = await _get_wishlist_rows(db, user_id)
	return _to_response(rows)


async def remove_from_wishlist(db: AsyncSession, user_id: UUID, product_id: UUID) -> None:
	stmt = delete(WishList).where(
		WishList.user_id == user_id,
		WishList.product_id == product_id,
	)
	result = await db.execute(stmt)
	await db.commit()

	if result.rowcount == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Wishlist item not found",
		)
