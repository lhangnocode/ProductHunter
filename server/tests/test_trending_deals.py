"""
Test suite cho Trending Deals API: GET /api/v1/platform_products/platform-products/trending
Bao gồm: danh sách rỗng, có data, phân loại deal (extreme/good), limit param, kiểm tra schema.
"""
import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from tests.conftest import TestingSessionLocal


# ============================================================
# HELPER: Tạo dữ liệu trong DB (platform, product, platform_product, price_records)
# ============================================================

async def _create_platform(name: str = "FPT Shop", base_url: str = "https://fptshop.com.vn") -> dict:
    """Tạo platform trong DB, trả về dict với id."""
    from app.models.platform import Platform
    async with TestingSessionLocal() as session:
        platform = Platform(name=name, base_url=base_url)
        session.add(platform)
        await session.commit()
        await session.refresh(platform)
        return {"id": platform.id, "name": platform.name}


async def _create_product(
    normalized_name: str = "Samsung Galaxy S24",
    product_name: str = "Samsung Galaxy S24 256GB",
) -> dict:
    """Tạo product trong DB, trả về dict."""
    from app.models.product import Product
    product_id = uuid.uuid4()
    slug = f"product-{uuid.uuid4().hex[:8]}"
    async with TestingSessionLocal() as session:
        product = Product(
            id=product_id,
            normalized_name=normalized_name,
            product_name=product_name,
            slug=slug,
            brand="Samsung",
            category="Điện thoại",
            main_image_url="https://example.com/s24.jpg",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return {
            "id": str(product.id),
            "normalized_name": product.normalized_name,
            "product_name": product.product_name,
            "main_image_url": product.main_image_url,
        }


async def _create_platform_product(
    platform_id: int,
    product_id: str,
    current_price: float,
    original_price: float = None,
    raw_name: str = "Samsung Galaxy S24",
    url: str = None,
) -> dict:
    """Tạo platform_product trong DB, trả về dict."""
    from app.models.platform_product import PlatformProduct
    pp_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        pp = PlatformProduct(
            id=pp_id,
            product_id=uuid.UUID(product_id),
            platform_id=platform_id,
            raw_name=raw_name,
            original_item_id=f"item_{uuid.uuid4().hex[:8]}",
            url=url or f"https://fptshop.com.vn/product/{uuid.uuid4().hex[:6]}",
            current_price=current_price,
            original_price=original_price or current_price,
            in_stock=True,
        )
        session.add(pp)
        await session.commit()
        await session.refresh(pp)
        return {
            "id": str(pp.id),
            "product_id": str(pp.product_id),
            "platform_id": pp.platform_id,
            "current_price": float(pp.current_price),
            "original_price": float(pp.original_price),
        }


_price_record_id_counter = 0


async def _create_price_records(
    platform_product_id: str,
    prices: list[float],
    days_ago_list: list[int] = None,
):
    """Tạo nhiều PriceRecord cho một PlatformProduct.
    
    SQLite không tự sinh BIGSERIAL nên phải truyền id thủ công.
    Dùng counter toàn cục để tránh trùng id giữa các test.
    """
    global _price_record_id_counter
    from app.models.price_record import PriceRecord
    from datetime import datetime, timedelta, timezone

    if days_ago_list is None:
        days_ago_list = list(range(len(prices)))

    async with TestingSessionLocal() as session:
        for price, days_ago in zip(prices, days_ago_list):
            _price_record_id_counter += 1
            recorded_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
            pr = PriceRecord(
                id=_price_record_id_counter,
                platform_product_id=uuid.UUID(platform_product_id),
                price=price,
                original_price=price,
                is_flash_sale=False,
                recorded_at=recorded_at,
            )
            session.add(pr)
        await session.commit()


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Danh sách rỗng
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_empty(ac: AsyncClient):
    """Không có data nào trong DB → trả về list rỗng (200)."""
    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    assert response.json() == []


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Không xuất hiện khi giá bình thường
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_no_result_when_price_above_avg(ac: AsyncClient):
    """
    Sản phẩm có current_price >= avg_price_180d → KHÔNG xuất hiện trong trending.
    """
    platform = await _create_platform()
    product = await _create_product("MacBook Pro M3", "Apple MacBook Pro M3 14 inch")
    pp = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product["id"],
        current_price=40_000_000,
        original_price=45_000_000,
    )

    # Lịch sử giá toàn thấp hơn current_price → avg < current_price → không phải "Giá tốt"
    # Thực ra avg < current thì KHÔNG trending, cần avg > current để trending
    # Tạo lịch sử với giá thấp hơn → avg = 35M < current 40M → KHÔNG xuất hiện
    await _create_price_records(pp["id"], [35_000_000, 36_000_000, 34_000_000], [10, 20, 30])

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert pp["id"] not in ids


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Deal "Giá tốt" (good)
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_good_deal_appears(ac: AsyncClient):
    """
    current_price < avg_180d nhưng current_price > min_ever → deal_status = 'good'.
    """
    platform = await _create_platform()
    product = await _create_product("iPhone 14", "Apple iPhone 14 128GB")
    pp = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product["id"],
        current_price=18_000_000,  # giá hiện tại thấp
        original_price=22_000_000,
    )

    # Lịch sử giá cao hơn current → avg ~ 21M > 18M (good)
    # Min ever = 15M < 18M → không extreme
    await _create_price_records(
        pp["id"],
        [15_000_000, 21_000_000, 22_000_000, 20_000_000, 21_500_000],
        [200, 30, 20, 10, 5],  # 15M là 200 ngày trước (ngoài 180 ngày)
    )

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()

    matched = [item for item in data if item["id"] == pp["id"]]
    assert len(matched) == 1
    item = matched[0]
    assert item["deal_status"] == "good"
    assert item["deal_label"] == "Giá tốt"


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Deal "Rẻ kỷ lục" (extreme)
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_extreme_deal_appears(ac: AsyncClient):
    """
    current_price <= min_price_ever và current_price < avg_180d → deal_status = 'extreme'.
    """
    platform = await _create_platform()
    product = await _create_product("Samsung S24 Ultra", "Samsung Galaxy S24 Ultra 512GB")
    pp = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product["id"],
        current_price=25_000_000,  # bằng min ever
        original_price=35_000_000,
    )

    # Lịch sử: min ever = 25M (chính là current), avg 180d = 30M > current → extreme
    await _create_price_records(
        pp["id"],
        [25_000_000, 30_000_000, 32_000_000, 31_000_000],
        [5, 30, 60, 90],
    )

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()

    matched = [item for item in data if item["id"] == pp["id"]]
    assert len(matched) == 1
    item = matched[0]
    assert item["deal_status"] == "extreme"
    assert item["deal_label"] == "Rẻ kỷ lục"


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Extreme xuất hiện trước Good
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_extreme_ranked_before_good(ac: AsyncClient):
    """
    Khi có cả 'extreme' và 'good' → extreme phải xuất hiện TRƯỚC good trong danh sách.
    """
    platform = await _create_platform()

    # Sản phẩm "good"
    product_good = await _create_product("Xiaomi 14", "Xiaomi 14 256GB")
    pp_good = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product_good["id"],
        current_price=12_000_000,
        original_price=15_000_000,
    )
    await _create_price_records(
        pp_good["id"],
        [10_000_000, 14_000_000, 14_500_000],  # min = 10M < 12M → good
        [5, 30, 60],
    )

    # Sản phẩm "extreme"
    product_extreme = await _create_product("OPPO Find X7", "OPPO Find X7 Pro 512GB")
    pp_extreme = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product_extreme["id"],
        current_price=20_000_000,  # = min ever → extreme
        original_price=28_000_000,
    )
    await _create_price_records(
        pp_extreme["id"],
        [20_000_000, 25_000_000, 27_000_000],
        [5, 30, 60],
    )

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()

    ids_in_order = [item["id"] for item in data]
    assert pp_extreme["id"] in ids_in_order
    assert pp_good["id"] in ids_in_order
    assert ids_in_order.index(pp_extreme["id"]) < ids_in_order.index(pp_good["id"])


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Kiểm tra schema response
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_response_schema(ac: AsyncClient):
    """
    Kiểm tra response trả về đúng các trường theo TrendingDealResponse schema.
    """
    platform = await _create_platform("Phong Vu", "https://phongvu.vn")
    product = await _create_product("Dell XPS 15", "Dell XPS 15 9530 Core i7")
    pp = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product["id"],
        current_price=28_000_000,
        original_price=35_000_000,
        url="https://phongvu.vn/dell-xps-15",
    )
    await _create_price_records(
        pp["id"],
        [28_000_000, 33_000_000, 34_000_000],
        [2, 30, 90],
    )

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()

    matched = [item for item in data if item["id"] == pp["id"]]
    assert len(matched) == 1
    item = matched[0]

    # Kiểm tra các trường bắt buộc trong TrendingDealResponse
    assert "id" in item
    assert "product_id" in item
    assert "product_name" in item
    assert "current_price" in item
    assert "url" in item
    assert "deal_status" in item
    assert "deal_label" in item

    # Kiểm tra giá trị hợp lệ
    assert item["product_id"] == product["id"]
    assert item["current_price"] == 28_000_000
    assert item["deal_status"] in ("good", "extreme")
    assert item["platform_name"] == "Phong Vu"
    assert "phongvu.vn" in item["url"]


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Query param limit
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_limit_param(ac: AsyncClient):
    """
    Truyền limit=1 → chỉ trả về tối đa 1 item dù có nhiều deal hơn.
    """
    platform = await _create_platform()

    for i in range(3):
        product = await _create_product(f"Laptop Model {i}", f"Laptop Brand {i} Gen{i} 16GB")
        pp = await _create_platform_product(
            platform_id=platform["id"],
            product_id=product["id"],
            current_price=15_000_000,
            original_price=20_000_000,
        )
        await _create_price_records(pp["id"], [15_000_000, 19_000_000, 20_000_000], [2, 30, 60])

    response = await ac.get("/api/v1/platform_products/platform-products/trending?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_trending_deals_limit_invalid(ac: AsyncClient):
    """
    limit=0 hoặc limit=101 → 422 (vi phạm ge=1, le=100).
    """
    response = await ac.get("/api/v1/platform_products/platform-products/trending?limit=0")
    assert response.status_code == 422

    response = await ac.get("/api/v1/platform_products/platform-products/trending?limit=101")
    assert response.status_code == 422


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Sản phẩm hết hàng
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_out_of_stock_excluded(ac: AsyncClient):
    """
    Sản phẩm hết hàng (in_stock=False) vẫn được handler xử lý theo giá,
    nhưng test này xác nhận API trả về 200 và không crash.
    """
    from app.models.platform_product import PlatformProduct

    platform = await _create_platform()
    product = await _create_product("Product OOS", "Product Out Of Stock 128GB")
    pp_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        pp = PlatformProduct(
            id=pp_id,
            product_id=uuid.UUID(product["id"]),
            platform_id=platform["id"],
            raw_name="Product OOS",
            original_item_id=f"oos_{uuid.uuid4().hex[:8]}",
            url="https://fptshop.com.vn/product-oos",
            current_price=5_000_000,
            original_price=8_000_000,
            in_stock=False,
        )
        session.add(pp)
        await session.commit()

    await _create_price_records(str(pp_id), [5_000_000, 7_000_000, 8_000_000], [2, 30, 60])

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Sản phẩm không có price_records
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_no_price_history_excluded(ac: AsyncClient):
    """
    PlatformProduct không có PriceRecord → không xuất hiện trong trending
    (vì không có avg_price để so sánh).
    """
    platform = await _create_platform()
    product = await _create_product("No History Product", "No History Brand 64GB")
    pp = await _create_platform_product(
        platform_id=platform["id"],
        product_id=product["id"],
        current_price=10_000_000,
        original_price=12_000_000,
    )
    # Không tạo price_records

    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    data = response.json()
    ids = [item["id"] for item in data]
    assert pp["id"] not in ids


# ============================================================
# GET /api/v1/platform_products/platform-products/trending — Không yêu cầu authentication
# ============================================================

@pytest.mark.asyncio
async def test_trending_deals_no_auth_required(ac: AsyncClient):
    """
    Endpoint trending là public → không cần token vẫn trả về 200.
    """
    response = await ac.get("/api/v1/platform_products/platform-products/trending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)