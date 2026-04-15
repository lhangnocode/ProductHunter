# app/api/products.py

import math
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
import json
import os
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import false, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db

from app.handlers.handler_product import search_product
from app.models.product import Product
from app.schemas.product import ProductResponse, SearchPaginatedResponse
from app.models.platform_product import PlatformProduct
from app.schemas.product import ProductCompareGroup, ProductResponse, SearchCompareResponse, ProductSearchItem
from app.schemas.platform import PlatformPriceItem
from sqlalchemy.orm import selectinload



router = APIRouter()

#! Khong lay bien tu env theo cach nay. Load tu config ra
# current_file = Path(__file__).resolve()
# server_dir = current_file.parents[3] 
# MOCK_FILE_PATH = server_dir / "mock_data" / "mock_platform_data.json"
# def load_mock_data():
#     try:
#         with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         print(f"Không tìm thấy file JSON tại: {MOCK_FILE_PATH}")
#         return []


# MOCK_PLATFORM_DATA = load_mock_data()
MOCK_PLATFORM_DATA = [
   {
    "product_id": "32918c2b-6f9f-4f67-a907-f4e9a68b16f7",
    "platform_id": 1,
    "raw_name": "Xiaomi POCO M7 Pro 5G (8GB/256GB) Màn hình 120Hz Camera 64MP",
    "original_item_id": "sp_3291_01",
    "url": "https://shopee.vn/xiaomi-poco-m7-pro-5g",
    "affiliate_url": "https://shopee.vn/xiaomi-poco-m7-pro-5g?utm_source=producthunter&aff_sub=ID",
    "current_price": 5200000,
    "original_price": 5990000,
    "in_stock": true,
    "last_crawled_at": "2026-03-29T10:00:00.000Z"
  },
  {
    "product_id": "32918c2b-6f9f-4f67-a907-f4e9a68b16f7",
    "platform_id": 2,
    "raw_name": "Điện Thoại Xiaomi POCO M7 Pro 5G 8GB/256GB - Hàng Chính Hãng",
    "original_item_id": "tk_3291_02",
    "url": "https://tiki.vn/xiaomi-poco-m7-pro",
    "affiliate_url": "https://tiki.vn/xiaomi-poco-m7-pro?utm_source=producthunter&aff_sub=ID",
    "current_price": 5350000,
    "original_price": 5990000,
    "in_stock": true,
    "last_crawled_at": "2026-03-29T10:00:00.000Z"
  },
  {
    "product_id": "32918c2b-6f9f-4f67-a907-f4e9a68b16f7",
    "platform_id": 5,
    "raw_name": "Xiaomi POCO M7 Pro 5G 8GB 256GB",
    "original_item_id": "cps_3291_03",
    "url": "https://cellphones.com.vn/xiaomi-poco-m7-pro",
    "affiliate_url": "https://cellphones.com.vn/xiaomi-poco-m7-pro?utm_source=producthunter&cps_aff=ID",
    "current_price": 5490000,
    "original_price": 5990000,
    "in_stock": true,
    "last_crawled_at": "2026-03-29T10:00:00.000Z"
  },
  {
    "product_id": "32918c2b-6f9f-4f67-a907-f4e9a68b16f7",
    "platform_id": 7,
    "raw_name": "Xiaomi POCO M7 Pro 5G 8GB-256GB Đen",
    "original_item_id": "fpt_3291_04",
    "url": "https://fptshop.com.vn/dien-thoai/xiaomi-poco-m7-pro",
    "affiliate_url": "https://fptshop.com.vn/dien-thoai/xiaomi-poco-m7-pro?utm_source=producthunter",
    "current_price": 5690000,
    "original_price": 5990000,
    "in_stock": false,
    "last_crawled_at": "2026-03-29T10:00:00.000Z"
  }
]

@router.get("/search", response_model=SearchPaginatedResponse)
async def search_products_list(
    q: str = Query(..., min_length=2, description="Keyword"),
    page: int = Query(1, ge=1, description="current page"),
    limit: int = Query(20, ge=1, le=100, description="num of products per page"),
    db: AsyncSession = Depends(get_db),
):
    products, total_results = await search_product(query=q, db=db, limit=limit, page=page)
    
    total_pages = math.ceil(total_results / limit) if total_results > 0 else 0

    return {
        "keyword": q,
        "current_page": page,
        "total_pages": total_pages,
        "total_results": total_results, 
        "data": products 
    }


@router.get("/")
async def get_all_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    return products

@router.get("/searchAll", response_model=SearchPaginatedResponse)
async def search_products_list(
    q: str = Query(..., min_length=2, description="Keyword"),
    page: int = Query(1, ge=1, description="current page"),
    limit: int = Query(20, ge=1, le=100, description="num of products per page"),
    db: AsyncSession = Depends(get_db),
):
    products, total_results = await search_product(query=q, db=db, limit=limit, page=page)
    
    total_pages = math.ceil(total_results / limit) if total_results > 0 else 0

    platform_items = []
    for p in products:
        if p.platform_products:
            platform_items.extend(p.platform_products)

    return {
        "keyword": q,
        "current_page": page,
        "total_pages": total_pages,
        "total_results": total_results, 
        "data": platform_items 
    }



from fastapi import Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
# Import các schema và dependency cần thiết của bạn ở đây...

@router.get("/compare", response_model=SearchCompareResponse)
async def search_and_compare_products(
    q: str = Query(..., min_length=2, description="Keyword"),
    db: AsyncSession = Depends(get_db),
):
    products, total_results = await search_product(query=q, db=db, limit=50, page=1)

    response_list = []
    
    for product in products:
        platforms_data = []
        valid_prices = []
        
        if getattr(product, "platform_products", None):
            for pp in product.platform_products:
                platforms_data.append(
                    PlatformPriceItem(
                        platform_id=pp.platform_id,
                        url=pp.url,
                        affiliate_url=pp.affiliate_url,
                        current_price=pp.current_price,
                        original_price=pp.original_price,
                        in_stock=pp.in_stock,
                        last_crawled_at=pp.last_crawled_at
                    )
                )
                if pp.in_stock and pp.current_price is not None:
                    valid_prices.append(pp.current_price)

        lowest_price = min(valid_prices) if valid_prices else None
        
        response_list.append(
            ProductCompareGroup(
                id=product.id,
                normalized_name=product.normalized_name,
                product_name=getattr(product, "product_name", None),
                slug=product.slug,
                main_image_url=product.main_image_url,
                lowest_price=lowest_price,
                platforms=platforms_data
            )
        )

    response_list.sort(key=lambda x: x.lowest_price if x.lowest_price is not None else float('inf'))

    return SearchCompareResponse(
        keyword=q,
        total_results=total_results,
        data=response_list
    )

@router.get("/compare2", response_model=SearchCompareResponse)
async def search_and_compare_mock(
    q: str = Query(..., min_length=2, description="Từ khóa tìm kiếm"),
    db: AsyncSession = Depends(get_db) 
):
    print(f"\n{'='*40}")
    print(f" BẮT ĐẦU TÌM KIẾM VỚI TỪ KHÓA: '{q}'")
    print(f" Số dữ liệu đang có trong file JSON: {len(MOCK_PLATFORM_DATA)} records")
    print(f"{'='*40}")

    # 1. Tìm trong DB
    query = select(Product).where(Product.normalized_name.ilike(f"%{q}%"))
    result = await db.execute(query)
    db_products = result.scalars().all()

    print(f" Bước 1: Database tìm thấy {len(db_products)} sản phẩm khớp từ khóa.")
    
    matched_groups = []

    for product in db_products:
        product_id_str = str(product.id)
        print(f"    Check DB Product: [{product.normalized_name}] | ID: {product_id_str}")
        
        # 2. Tìm trong JSON
        platforms_for_this_product = [
            item for item in MOCK_PLATFORM_DATA 
            if str(item.get("product_id")).strip().lower() == product_id_str.strip().lower()
        ]

        print(f"    Có {len(platforms_for_this_product)} link sàn khớp với ID này trong JSON.")

        if not platforms_for_this_product:
            print("   BỎ QUA vì không có link sàn nào!")
            continue

        lowest_price = min(
            p["current_price"] for p in platforms_for_this_product 
            if p.get("current_price") is not None
        )

        group = ProductCompareGroup(
            id=product.id,
            normalized_name=product.normalized_name,
            product_name=getattr(product, "product_name", None),
            slug=product.slug if hasattr(product, 'slug') else "slug-tam",
            main_image_url=product.image_url if hasattr(product, 'image_url') else None,
            lowest_price=lowest_price,
            platforms=platforms_for_this_product
        )
        matched_groups.append(group)

    print(f" KẾT LUẬN: Trả về cho Frontend {len(matched_groups)} nhóm sản phẩm.\n")

    matched_groups.sort(key=lambda x: x.lowest_price if x.lowest_price else 999999999)

    return SearchCompareResponse(
        keyword=q,
        total_results=len(matched_groups),
        data=matched_groups
    )

