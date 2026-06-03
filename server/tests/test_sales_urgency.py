from datetime import datetime, timedelta, timezone

from app.agent.sales.urgency import build_urgency_cues


def _recent_iso(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_fresh_stock_cue_emitted():
    offer = {"in_stock": True, "last_crawled_at": _recent_iso(0)}
    cues = build_urgency_cues(offer, None)
    assert any("Cập nhật" in cue for cue in cues)


def test_lowest_in_90_days_emitted():
    offer = {"in_stock": True, "price": 10_000_000}
    history = {"min_90d": 10_000_000, "trend": "flat"}
    cues = build_urgency_cues(offer, history)
    assert any("thấp nhất 90 ngày" in cue for cue in cues)


def test_falling_trend_emitted():
    offer = {"in_stock": True, "price": 10_000_000}
    history = {"min_90d": 11_000_000, "trend": "falling"}
    cues = build_urgency_cues(offer, history)
    assert any("xu hướng giảm" in cue for cue in cues)


def test_no_cues_without_data():
    offer = {"in_stock": True, "price": 10_000_000}
    assert build_urgency_cues(offer, None) == []


def test_out_of_stock_yields_no_freshness_cue():
    offer = {"in_stock": False, "last_crawled_at": _recent_iso(0)}
    cues = build_urgency_cues(offer, None)
    assert not any("Cập nhật" in cue for cue in cues)


def test_naive_datetime_string_is_handled():
    naive = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
    offer = {"in_stock": True, "last_crawled_at": naive}
    cues = build_urgency_cues(offer, None)
    assert any("Cập nhật" in cue for cue in cues)
