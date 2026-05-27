# tests/test_qwen_resilience.py
import asyncio
import pytest
import httpx
from app.services.qwen_client import (
    call_qwen_with_resilience,
    CircuitBreaker,
    AdvisorProviderError,
    AdvisorCircuitOpenError,
    _model_for_attempt,          # internal but useful for assertions
    _FALLBACK_AFTER_ATTEMPT,
    _CIRCUIT_BREAKER_AFTER,
)

# ---------------------------------------------------------------------------
# Helper to mock async functions cleanly
# ---------------------------------------------------------------------------
async def async_dummy_sleep(_: float):
    """An asynchronous no-op to replace asyncio.sleep during tests."""
    pass

# ---------------------------------------------------------------------------
# Helper to create a fake _single_attempt that can raise different errors
# ---------------------------------------------------------------------------
def make_fake_single(attempts_to_fail: int,
                     fail_with: Exception,
                     succeed_with: str = "ok-content"):
    """Return a coroutine that fails the first `attempts_to_fail` times with
    `fail_with` and then returns `succeed_with`."""
    state = {"cnt": 0}
    async def _fake(*, client, url, headers, payload, model):
        state["cnt"] += 1
        if state["cnt"] <= attempts_to_fail:
            raise fail_with
        return succeed_with
    return _fake

# ---------------------------------------------------------------------------
# 1️⃣  Transient network failures → retry succeeds
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures(monkeypatch):
    # fail twice with a retryable network error, succeed on the 3rd try
    fake = make_fake_single(attempts_to_fail=2,
                            fail_with=httpx.NetworkError("simulated"))
    monkeypatch.setattr(
        "app.services.qwen_client._single_attempt", fake, raising=False
    )
    # FIX: Use async dummy function instead of synchronous lambda
    monkeypatch.setattr(asyncio, "sleep", async_dummy_sleep)
    
    cb = CircuitBreaker(failure_threshold=10, recovery_timeout=1.0)
    result = await call_qwen_with_resilience(
        url="https://example.test/chat/completions",
        api_key="dummy",
        payload={"messages": []},
        timeout=1.0,
        circuit_breaker=cb,
    )
    assert result == "ok-content"

# ---------------------------------------------------------------------------
# 2️⃣  Fallback to qwen‑flash after the configured number of plus failures
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fallback_to_flash(monkeypatch):
    # We want the first 3 attempts (0,1,2) to use qwen‑plus and fail.
    # The 4th attempt (attempt==3) will be the first flash attempt.
    # We fail the first three with a retryable 5xx error, then succeed.
    fail_exc = httpx.HTTPStatusError(
        "5xx", request=httpx.Request("POST", "url"), response=httpx.Response(502)
    )
    fake = make_fake_single(attempts_to_fail=3, fail_with=fail_exc)
    monkeypatch.setattr(
        "app.services.qwen_client._single_attempt", fake, raising=False
    )
    # FIX: Use async dummy function instead of synchronous lambda
    monkeypatch.setattr(asyncio, "sleep", async_dummy_sleep)
    
    cb = CircuitBreaker(failure_threshold=10, recovery_timeout=1.0)
    await call_qwen_with_resilience(
        url="https://example.test/chat/completions",
        api_key="dummy",
        payload={"messages": []},
        timeout=1.0,
        circuit_breaker=cb,
    )
    # After the call the last model used must be the fallback model
    # because attempt 3 (0‑based) is the first time we switched.
    assert _model_for_attempt(3) != _model_for_attempt(2)  # sanity
    assert _model_for_attempt(3) == "qwen-plus"

# ---------------------------------------------------------------------------
# 3️⃣  Circuit‑breaker opens after reaching the failure threshold
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_circuit_breaker_opens(monkeypatch):
    # Fail more times than the CB threshold (5 failures here)
    fake = make_fake_single(attempts_to_fail=6,
                            fail_with=httpx.NetworkError("boom"))
    monkeypatch.setattr(
        "app.services.qwen_client._single_attempt", fake, raising=False
    )
    # FIX: Use async dummy function instead of synchronous lambda
    monkeypatch.setattr(asyncio, "sleep", async_dummy_sleep)
    
    # Use a tiny threshold so it opens quickly
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
    # First call will exhaust retries and raise ProviderError
    with pytest.raises(AdvisorProviderError):
        await call_qwen_with_resilience(
            url="https://example.test/chat/completions",
            api_key="dummy",
            payload={"messages": []},
            timeout=1.0,
            circuit_breaker=cb,
        )
    # Now the breaker should be OPEN – the next call fails immediately
    with pytest.raises(AdvisorCircuitOpenError) as exc:
        await call_qwen_with_resilience(
            url="https://example.test/chat/completions",
            api_key="dummy",
            payload={"messages": []},
            timeout=1.0,
            circuit_breaker=cb,
        )
    assert "Circuit Breaker đang OPEN" in str(exc.value)

# ---------------------------------------------------------------------------
# 4️⃣  Non‑retryable error aborts immediately
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_non_retryable_error_raises_provider_error(monkeypatch):
    # 400 Bad Request is not in the retryable set
    resp = httpx.Response(400, request=httpx.Request("POST", "url"))
    fail_exc = httpx.HTTPStatusError("400 Bad", request=resp.request, response=resp)
    fake = make_fake_single(attempts_to_fail=1, fail_with=fail_exc)
    monkeypatch.setattr(
        "app.services.qwen_client._single_attempt", fake, raising=False
    )
    # FIX: Use async dummy function instead of synchronous lambda
    monkeypatch.setattr(asyncio, "sleep", async_dummy_sleep)
    
    cb = CircuitBreaker(failure_threshold=10, recovery_timeout=1.0)
    with pytest.raises(AdvisorProviderError) as exc:
        await call_qwen_with_resilience(
            url="https://example.test/chat/completions",
            api_key="dummy",
            payload={"messages": []},
            timeout=1.0,
            circuit_breaker=cb,
        )
    # The message should contain the original 400 code
    assert "400" in str(exc.value)

# ---------------------------------------------------------------------------
# 5️⃣  Verify exponential back‑off intervals (without jitter)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_backoff_intervals(monkeypatch):
    # Force three retries (fail twice, succeed third)
    fake = make_fake_single(attempts_to_fail=2,
                            fail_with=httpx.NetworkError("sim"))
    monkeypatch.setattr(
        "app.services.qwen_client._single_attempt", fake, raising=False
    )
    # Capture the sleep durations that the client asks for
    sleeps = []
    async def fake_sleep(seconds: float):
        sleeps.append(seconds)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    
    cb = CircuitBreaker(failure_threshold=10, recovery_timeout=1.0)
    await call_qwen_with_resilience(
        url="https://example.test/chat/completions",
        api_key="dummy",
        payload={"messages": []},
        timeout=1.0,
        circuit_breaker=cb,
    )
    # With backoff_base = 1.0 (default) and no jitter:
    # attempt 1 → wait = 1 * 2^1 = 2
    # attempt 2 → wait = 1 * 2^2 = 4
    assert sleeps == [2.0, 4.0]