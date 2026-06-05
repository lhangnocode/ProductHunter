import pytest

from app.jobs import price_alert_worker


@pytest.mark.asyncio
async def test_worker_run_once_calls_alert_check_and_logs(monkeypatch, caplog):
    class _FakeSession:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class _FakeSessionmaker:
        def __call__(self):
            return _FakeSession()

    async def _fake_check(db):
        return {
            "checked_products": 2,
            "triggered_alerts": 1,
            "email_queued": 1,
            "fcm_sent": 1,
            "invalid_tokens": 0,
            "skipped_without_price": 1,
        }

    monkeypatch.setattr(price_alert_worker, "check_and_trigger_system_alerts", _fake_check)
    monkeypatch.setattr(price_alert_worker, "get_sessionmaker", lambda: _FakeSessionmaker())

    with caplog.at_level("INFO"):
        result = await price_alert_worker.run_once()

    assert result["triggered_alerts"] == 1
    assert "price_alert_worker checked=2 triggered=1" in caplog.text
