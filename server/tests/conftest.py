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
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def ac() -> AsyncClient:
    """Khởi tạo AsyncClient để gọi API cục bộ theo chuẩn FastAPI mới nhất"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
