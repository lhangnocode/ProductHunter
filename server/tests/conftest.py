import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from main import app
from app.db.session import Base, get_db
import warnings
from pydantic import warnings as pydantic_warnings

# Tắt các cảnh báo Pydantic trong pytest (BaseSettings deprecated, ...)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="pydantic")

# Sử dụng SQLite file thay vì in-memory để tránh deadlock khi chạy test bất đồng bộ
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_runner.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Tạo schema CSDL SQLite trước khi chạy toàn bộ test"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    """Xóa toàn bộ dữ liệu sau mỗi test để đảm bảo test isolation."""
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest_asyncio.fixture
async def ac() -> AsyncClient:
    """Khởi tạo AsyncClient để gọi API cục bộ theo chuẩn FastAPI mới nhất"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ============================================================
# HELPER: Đăng ký + đăng nhập → trả về headers Authorization
# ============================================================
async def _register_and_login(
    ac: AsyncClient, email: str, password: str, full_name: str = "Test User", plan: int = 0
) -> dict:
    """Đăng ký user, (tùy chọn) nâng plan, đăng nhập và trả về header."""
    await ac.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
    })

    # Nếu cần plan Premium → cập nhật trực tiếp qua DB
    if plan == 1:
        async with TestingSessionLocal() as session:
            from sqlalchemy import update, select
            from app.models.user import User
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.plan = 1
                await session.commit()

    login_resp = await ac.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers(ac: AsyncClient) -> dict:
    """Headers cho user Free (plan=0)."""
    return await _register_and_login(
        ac, email="testuser@example.com", password="Test@1234", full_name="Test User", plan=0
    )


@pytest_asyncio.fixture
async def premium_auth_headers(ac: AsyncClient) -> dict:
    """Headers cho user Premium (plan=1)."""
    return await _register_and_login(
        ac, email="premiumuser@example.com", password="Premium@1234", full_name="Premium User", plan=1
    )


# ============================================================
# HELPER: Tạo Platform qua API → trả về response dict
# ============================================================
@pytest_asyncio.fixture
async def created_platform(ac: AsyncClient) -> dict:
    """Tạo sẵn 1 platform Shopee để dùng trong các test khác."""
    resp = await ac.post("/api/v1/platforms/", json={
        "name": "Shopee",
        "base_url": "https://shopee.vn",
    })
    assert resp.status_code == 201
    return resp.json()


# ============================================================
# HELPER: Tạo Product trực tiếp trong DB → trả về dict
# ============================================================
@pytest_asyncio.fixture
async def created_product() -> dict:
    """Tạo sẵn 1 product trong DB (bypass API vì products API không có endpoint tạo trực tiếp)."""
    import uuid
    product_id = uuid.uuid4()
    slug_suffix = uuid.uuid4().hex[:8]
    async with TestingSessionLocal() as session:
        from app.models.product import Product
        product = Product(
            id=product_id,
            normalized_name="iPhone 15 Pro Max",
            product_name="Apple iPhone 15 Pro Max 256GB",
            slug=f"iphone-15-pro-max-{slug_suffix}",
            brand="Apple",
            category="Điện thoại",
            main_image_url="https://example.com/iphone15.jpg",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return {
            "id": str(product.id),
            "normalized_name": product.normalized_name,
            "product_name": product.product_name,
            "slug": product.slug,
            "brand": product.brand,
            "category": product.category,
            "main_image_url": product.main_image_url,
        }


# ============================================================
# HELPER: Tạo PlatformProduct trực tiếp trong DB
# ============================================================
@pytest_asyncio.fixture
async def created_platform_product(created_platform: dict, created_product: dict) -> dict:
    """Tạo sẵn 1 PlatformProduct trong DB."""
    import uuid
    pp_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        from app.models.platform_product import PlatformProduct
        pp = PlatformProduct(
            id=pp_id,
            product_id=created_product["id"],
            platform_id=created_platform["id"],
            raw_name="iPhone 15 Pro Max - Shopee",
            original_item_id="shopee_ip15_001",
            url="https://shopee.vn/iphone-15-pro-max",
            affiliate_url="https://shopee.vn/iphone-15-pro-max?aff=123",
            current_price=28990000,
            original_price=34990000,
            in_stock=True,
        )
        session.add(pp)
        await session.commit()
        await session.refresh(pp)
        return {
            "id": str(pp.id),
            "product_id": str(pp.product_id),
            "platform_id": pp.platform_id,
            "raw_name": pp.raw_name,
            "original_item_id": pp.original_item_id,
            "url": pp.url,
            "current_price": float(pp.current_price),
            "original_price": float(pp.original_price),
        }
