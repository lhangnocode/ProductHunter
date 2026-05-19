import pytest
import uuid
from datetime import datetime, timedelta, timezone
from app.handlers.handler_price_record import analyze_price_status
from app.models.price_record import PriceRecord
from tests.conftest import TestingSessionLocal

# Biến đếm toàn cục để cấp ID thủ công cho SQLite trong môi trường test
_price_record_id_counter = 0

# ============================================================
# HELPER: Tạo lịch sử giá
# ============================================================
async def _create_history(pp_id: uuid.UUID, prices: list[float], days_ago_list: list[int]):
    global _price_record_id_counter
    async with TestingSessionLocal() as session:
        for price, days_ago in zip(prices, days_ago_list):
            _price_record_id_counter += 1
            recorded_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
            pr = PriceRecord(
                id=_price_record_id_counter, 
                platform_product_id=pp_id,
                price=price,
                original_price=price, # Để đơn giản trong lịch sử
                is_flash_sale=False,
                recorded_at=recorded_at
            )
            session.add(pr)
        await session.commit()

@pytest.mark.asyncio
async def test_analyze_no_history(ac):
    """Trường hợp chưa có lịch sử giá và không giảm giá -> Stable."""
    pp_id = uuid.uuid4()
    async with TestingSessionLocal() as db:
        # Để kết quả là 'stable', original_price PHẢI BẰNG current_price
        # Nếu original_price > current_price, handler sẽ trả về 'slight'
        result = await analyze_price_status(
            db, pp_id, current_price=100000, original_price=100000
        )
    
    assert result["deal_status"] == "stable"
    assert result["deal_label"] == "Giá ổn định"

@pytest.mark.asyncio
async def test_analyze_extreme_deal(ac):
    """Trường hợp Rẻ kỷ lục."""
    pp_id = uuid.uuid4()
    await _create_history(pp_id, [100000, 110000, 90000], [10, 20, 30])
    
    async with TestingSessionLocal() as db:
        result = await analyze_price_status(
            db, pp_id, current_price=80000, original_price=120000
        )
    
    assert result["deal_status"] == "extreme"
    assert result["deal_label"] == "Rẻ kỷ lục"

@pytest.mark.asyncio
async def test_analyze_good_deal(ac):
    """Trường hợp Giá tốt."""
    pp_id = uuid.uuid4()
    await _create_history(pp_id, [100000, 100000, 85000], [5, 10, 70])
    
    async with TestingSessionLocal() as db:
        result = await analyze_price_status(
            db, pp_id, current_price=90000, original_price=120000
        )
    
    assert result["deal_status"] == "good"

@pytest.mark.asyncio
async def test_analyze_fake_discount(ac):
    """Trường hợp Khuyến mãi ảo."""
    pp_id = uuid.uuid4()
    await _create_history(pp_id, [100000, 100000, 100000], [5, 10, 15])
    
    async with TestingSessionLocal() as db:
        result = await analyze_price_status(
            db, pp_id, current_price=120000, original_price=150000
        )
    
    assert result["deal_status"] == "fake"

@pytest.mark.asyncio
async def test_analyze_slight_deal(ac):
    """Trường hợp có giảm nhẹ (original > current nhưng ko đủ rẻ)."""
    pp_id = uuid.uuid4()
    await _create_history(pp_id, [98000, 98000], [5, 10])
    
    async with TestingSessionLocal() as db:
        result = await analyze_price_status(
            db, pp_id, current_price=98000, original_price=100000
        )
    
    assert result["deal_status"] == "slight"

@pytest.mark.asyncio
async def test_analyze_stable_price(ac):
    """Trường hợp giá ổn định (original == current và bằng trung bình)."""
    pp_id = uuid.uuid4()
    await _create_history(pp_id, [100000, 100000], [5, 10])
    
    async with TestingSessionLocal() as db:
        result = await analyze_price_status(
            db, pp_id, current_price=100000, original_price=100000
        )
    
    assert result["deal_status"] == "stable"