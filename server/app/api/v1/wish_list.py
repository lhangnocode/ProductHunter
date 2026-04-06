from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.wish_list import WishListCreate, WishListResponse
from app.services import wish_list as wish_list_service

router = APIRouter()


@router.post("/", response_model=WishListResponse)
async def create_wishlist_item(
    body: WishListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await wish_list_service.add_to_wishlist(
        db=db,
        user_id=current_user.id,
        product_id=body.product_id,
    )


@router.get("/", response_model=WishListResponse)
async def get_my_wishlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await wish_list_service.get_user_wishlist(
        db=db,
        user_id=current_user.id,
    )


@router.delete("/{product_id}")
async def delete_wishlist_item(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await wish_list_service.remove_from_wishlist(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )
    return {"message": "Removed from wishlist"}