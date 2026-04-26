"""
Test suite cho Price Record API: /api/v1/price_record/
Bao gồm: get all, get by platform_product_id, push single, push batch, price analysis.
"""
import pytest
from httpx import AsyncClient
import uuid


# ============================================================
# GET ALL — GET /api/v1/price_record/price-records
# ============================================================
@pytest.mark.asyncio
async def test_get_all_price_records_empty(ac: AsyncClient):
    """Danh sách rỗng khi chưa có data → 200."""
    response = await ac.get("/api/v1/price_record/price-records")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_price_records_with_params(ac: AsyncClient):
    """Kiểm tra limit/offset params → 200."""
    response = await ac.get("/api/v1/price_record/price-records?limit=5&offset=0")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_price_records_invalid_limit(ac: AsyncClient):
    """Limit ngoài phạm vi → 422."""
    response = await ac.get("/api/v1/price_record/price-records?limit=200")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_all_price_records_negative_offset(ac: AsyncClient):
    """Offset âm → 422."""
    response = await ac.get("/api/v1/price_record/price-records?offset=-1")
    assert response.status_code == 422


# ============================================================
# GET BY PLATFORM_PRODUCT_ID — GET /api/v1/price_record/price-records/{id}
# ============================================================
@pytest.mark.asyncio
async def test_get_price_records_by_id_empty(ac: AsyncClient):
    """UUID không tồn tại → 200 + list rỗng."""
    fake_id = str(uuid.uuid4())
    response = await ac.get(f"/api/v1/price_record/price-records/{fake_id}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_price_records_by_invalid_uuid(ac: AsyncClient):
    """UUID không hợp lệ → 422."""
    response = await ac.get("/api/v1/price_record/price-records/not-a-uuid")
    assert response.status_code == 422


# ============================================================
# PUSH SINGLE — POST /api/v1/price_record/price-records
# ============================================================
@pytest.mark.asyncio
async def test_push_price_record_not_found(ac: AsyncClient):
    """PlatformProduct không tồn tại → 404."""
    fake_pp_id = str(uuid.uuid4())
    response = await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": fake_pp_id,
        "price": 5000000,
        "original_price": 6000000,
        "is_flash_sale": False,
    })
    assert response.status_code == 404
    assert "PlatformProduct not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_push_price_record_success(ac: AsyncClient, created_platform_product: dict):
    """Tạo price record thành công → 201."""
    pp_id = created_platform_product["id"]
    response = await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": pp_id,
        "price": 28000000,
        "original_price": 34990000,
        "is_flash_sale": False,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["platform_product_id"] == pp_id
    assert float(data["price"]) == 28000000
    assert data["is_flash_sale"] is False


@pytest.mark.asyncio
async def test_push_price_record_flash_sale(ac: AsyncClient, created_platform_product: dict):
    """Tạo price record Flash Sale → 201."""
    pp_id = created_platform_product["id"]
    response = await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": pp_id,
        "price": 25000000,
        "original_price": 34990000,
        "is_flash_sale": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["is_flash_sale"] is True


@pytest.mark.asyncio
async def test_push_price_record_missing_price(ac: AsyncClient):
    """Thiếu trường price → 422."""
    response = await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": str(uuid.uuid4()),
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_push_price_record_with_timestamp(ac: AsyncClient, created_platform_product: dict):
    """Tạo price record kèm recorded_at → 201."""
    pp_id = created_platform_product["id"]
    response = await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": pp_id,
        "price": 27000000,
        "recorded_at": "2026-04-01T10:00:00Z",
    })
    assert response.status_code == 201
    data = response.json()
    assert "2026-04-01" in data["recorded_at"]


# ============================================================
# PUSH BATCH — POST /api/v1/price_record/price-records/batch
# ============================================================
@pytest.mark.asyncio
async def test_push_batch_empty(ac: AsyncClient):
    """Batch rỗng → 201 + list rỗng."""
    response = await ac.post("/api/v1/price_record/price-records/batch", json=[])
    assert response.status_code == 201
    assert response.json() == []


@pytest.mark.asyncio
async def test_push_batch_success(ac: AsyncClient, created_platform_product: dict):
    """Batch 2 records → 201 + 2 items."""
    pp_id = created_platform_product["id"]
    payload = [
        {
            "platform_product_id": pp_id,
            "price": 28000000,
            "original_price": 34990000,
            "is_flash_sale": False,
        },
        {
            "platform_product_id": pp_id,
            "price": 27500000,
            "original_price": 34990000,
            "is_flash_sale": True,
        },
    ]
    response = await ac.post("/api/v1/price_record/price-records/batch", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_push_batch_skip_invalid_pp(ac: AsyncClient):
    """Batch chứa PlatformProduct không tồn tại → bỏ qua, trả list rỗng."""
    fake_id = str(uuid.uuid4())
    payload = [
        {
            "platform_product_id": fake_id,
            "price": 1000000,
        }
    ]
    response = await ac.post("/api/v1/price_record/price-records/batch", json=payload)
    assert response.status_code == 201
    assert response.json() == []


# ============================================================
# GET PRICE RECORDS BY PLATFORM_PRODUCT — verify data exists after push
# ============================================================
@pytest.mark.asyncio
async def test_get_price_records_after_push(ac: AsyncClient, created_platform_product: dict):
    """Push rồi get → có data."""
    pp_id = created_platform_product["id"]

    # Push 1 record
    await ac.post("/api/v1/price_record/price-records", json={
        "platform_product_id": pp_id,
        "price": 26000000,
    })

    # Get records
    response = await ac.get(f"/api/v1/price_record/price-records/{pp_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(r["platform_product_id"] == pp_id for r in data)


# ============================================================
# PRICE ANALYSIS — GET /api/v1/price_record/price-analysis/{id}
# ============================================================
@pytest.mark.asyncio
async def test_price_analysis_endpoint(ac: AsyncClient, created_platform_product: dict):
    """Gọi price analysis → 200 (kết quả phụ thuộc handler logic)."""
    pp_id = created_platform_product["id"]
    response = await ac.get(
        f"/api/v1/price_record/price-analysis/{pp_id}?current_price=28000000&original_price=34990000"
    )
    # Endpoint chỉ cần trả về thành công
    assert response.status_code == 200
