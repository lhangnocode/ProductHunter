from app.agent.sales.deal_score import compute_deal_score


def _offer(**overrides):
    base = {
        "platform_product_id": "pp-1",
        "platform_id": 1,
        "platform_name": "CellphoneS",
        "price": 10_000_000,
        "original_price": 12_000_000,
        "in_stock": True,
    }
    base.update(overrides)
    return base


def test_strong_discount_with_history_increases_score():
    offer = _offer(price=10_000_000, original_price=15_000_000, in_stock=True)
    history = {"min_90d": 9_900_000, "avg_90d": 11_000_000, "trend": "falling"}
    result = compute_deal_score(offer, history)
    assert result["discount_pct"] == 33.3
    assert result["deal_score"] >= 80
    assert any("thấp nhất 90 ngày" in reason for reason in result["deal_reasons"])


def test_out_of_stock_penalizes_score():
    offer = _offer(price=10_000_000, original_price=10_000_000, in_stock=False)
    result = compute_deal_score(offer, None)
    assert result["deal_score"] < 50
    assert any("Tạm hết hàng" in reason for reason in result["deal_reasons"])


def test_no_history_still_scores_off_discount():
    offer = _offer(price=9_000_000, original_price=10_000_000, in_stock=True)
    result = compute_deal_score(offer, None)
    assert result["discount_pct"] == 10.0
    assert result["deal_score"] > 50


def test_score_is_bounded():
    offer = _offer(price=1, original_price=10_000_000, in_stock=True)
    history = {"min_90d": 1, "avg_90d": 5_000_000, "trend": "falling"}
    result = compute_deal_score(offer, history)
    assert 0 <= result["deal_score"] <= 100


def test_rising_trend_lowers_score_relative_to_flat():
    base_offer = _offer(price=10_000_000, original_price=10_000_000, in_stock=True)
    flat = compute_deal_score(base_offer, {"min_90d": 10_000_000, "avg_90d": 10_000_000, "trend": "flat"})
    rising = compute_deal_score(
        base_offer,
        {"min_90d": 10_000_000, "avg_90d": 10_000_000, "trend": "rising"},
    )
    assert rising["deal_score"] < flat["deal_score"]
