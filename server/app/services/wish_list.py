from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.platform_product import PlatformProduct
from app.models.wish_list import WishList
from app.schemas.wish_list import WishListItem, WishListResponse


async def _get_wishlist_rows(db: AsyncSession, user_id: UUID) -> List[WishList]:
	stmt = (
		select(WishList)
		.options(
			selectinload(WishList.product),
			selectinload(WishList.platform_product),
		)
		.where(WishList.user_id == user_id)
		.order_by(WishList.added_at.desc())
	)
	result = await db.execute(stmt)
	return list(result.scalars().all())


def _to_response(rows: List[WishList]) -> WishListResponse:
	items = [
		WishListItem(
			product_id=row.product_id,
			platform_product_id=row.platform_product_id,
			added_at=row.added_at,
			product_name=(
				row.platform_product.raw_name
				if row.platform_product and row.platform_product.raw_name
				else row.product.normalized_name if row.product else None
			),
			main_image_url=row.product.main_image_url if row.product else None,
			current_price=(
				float(row.platform_product.current_price)
				if row.platform_product and row.platform_product.current_price is not None
				else None
			),
			original_price=(
				float(row.platform_product.original_price)
				if row.platform_product and row.platform_product.original_price is not None
				else None
			),
		)
		for row in rows
	]
	return WishListResponse(items=items)


async def _resolve_platform_product(db: AsyncSession, product_id: UUID | None, platform_product_id: UUID | None) -> PlatformProduct:
	stmt = (
		select(PlatformProduct)
		.options(selectinload(PlatformProduct.product))
	)
	if platform_product_id is not None:
		stmt = stmt.where(PlatformProduct.id == platform_product_id)
	elif product_id is not None:
		stmt = (
			stmt.where(PlatformProduct.product_id == product_id)
			.order_by(PlatformProduct.current_price.asc(), PlatformProduct.id.desc())
			.limit(1)
		)
	else:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail="platform_product_id is required",
		)

	result = await db.execute(stmt)
	platform_product = result.scalar_one_or_none()
	if platform_product is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Platform product not found",
		)
	return platform_product


async def add_to_wishlist(
	db: AsyncSession,
	user_id: UUID,
	product_id: UUID | None = None,
	platform_product_id: UUID | None = None,
) -> WishListResponse:
	platform_product = await _resolve_platform_product(db, product_id, platform_product_id)

	existing_stmt = select(WishList).where(
		WishList.user_id == user_id,
		WishList.platform_product_id == platform_product.id,
	)
	existing_result = await db.execute(existing_stmt)
	if existing_result.scalar_one_or_none() is None:
		db.add(
			WishList(
				user_id=user_id,
				product_id=platform_product.product_id,
				platform_product_id=platform_product.id,
			)
		)

	await db.commit()

	rows = await _get_wishlist_rows(db, user_id)
	return _to_response(rows)


async def get_user_wishlist(db: AsyncSession, user_id: UUID) -> WishListResponse:
	rows = await _get_wishlist_rows(db, user_id)
	return _to_response(rows)


async def remove_from_wishlist(db: AsyncSession, user_id: UUID, platform_product_id: UUID) -> None:
	stmt = delete(WishList).where(
		WishList.user_id == user_id,
		WishList.platform_product_id == platform_product_id,
	)
	result = await db.execute(stmt)
	await db.commit()

	if result.rowcount == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Wishlist item not found",
		)
