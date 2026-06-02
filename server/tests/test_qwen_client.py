from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.advisor import AdvisorConfigurationError
from app.services.qwen_client import (
    AdvisorCircuitOpenError,
    AdvisorProviderError,
    CircuitBreaker,
    _FALLBACK_MODEL,
    _PRIMARY_MODEL,
    _is_retryable,
    _model_for_attempt,
    _single_attempt,
    call_qwen_with_resilience,
)


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, headers, json):
        self.posts.append((url, headers, json))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://qwen.example.test")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("provider error", request=request, response=response)


@pytest.mark.asyncio
async def test_circuit_breaker_closed_allows_requests():
    breaker = CircuitBreaker()

    assert await breaker.allow_request()
    assert breaker.state.value == "closed"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_at_failure_threshold_and_blocks():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    await breaker.record_failure()
    assert await breaker.allow_request()

    await breaker.record_failure()
    assert breaker.state.value == "open"
    assert not await breaker.allow_request()


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery_and_success_reset():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

    await breaker.record_failure()
    assert await breaker.allow_request()
    assert breaker.state.value == "half_open"

    await breaker.record_success()
    assert breaker.state.value == "closed"
    assert await breaker.allow_request()


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_reopens():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

    await breaker.record_failure()
    assert await breaker.allow_request()
    await breaker.record_failure()

    assert breaker.state.value == "open"


def test_is_retryable_classifies_provider_errors():
    assert _is_retryable(httpx.TimeoutException("slow"))
    assert _is_retryable(httpx.NetworkError("offline"))
    assert _is_retryable(_http_status_error(503))
    assert not _is_retryable(_http_status_error(400))
    assert not _is_retryable(ValueError("bad response"))


def test_model_for_attempt_switches_to_fallback():
    assert _model_for_attempt(0) == _PRIMARY_MODEL
    assert _model_for_attempt(2) == _PRIMARY_MODEL
    assert _model_for_attempt(3) == _FALLBACK_MODEL


@pytest.mark.asyncio
async def test_single_attempt_returns_trimmed_content():
    client = FakeClient([
        FakeResponse({"choices": [{"message": {"content": "  answer  "}}]}),
    ])

    result = await _single_attempt(
        client=client,
        url="https://qwen.example.test",
        headers={"Authorization": "Bearer key"},
        payload={"messages": []},
        model="qwen-flash",
    )

    assert result == "answer"
    assert client.posts[0][2]["model"] == "qwen-flash"


@pytest.mark.asyncio
async def test_single_attempt_rejects_invalid_json_shape():
    client = FakeClient([FakeResponse({"choices": []})])

    with pytest.raises(ValueError, match="invalid JSON structure"):
        await _single_attempt(
            client=client,
            url="https://qwen.example.test",
            headers={},
            payload={},
            model="qwen-flash",
        )


@pytest.mark.asyncio
async def test_single_attempt_rejects_empty_content():
    client = FakeClient([FakeResponse({"choices": [{"message": {"content": " "}}]})])

    with pytest.raises(ValueError, match="empty"):
        await _single_attempt(
            client=client,
            url="https://qwen.example.test",
            headers={},
            payload={},
            model="qwen-flash",
        )


@pytest.mark.asyncio
async def test_call_qwen_requires_api_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    with pytest.raises(AdvisorConfigurationError):
        await call_qwen_with_resilience(
            url="https://qwen.example.test",
            api_key=None,
            payload={"messages": []},
        )


@pytest.mark.asyncio
async def test_call_qwen_success(monkeypatch):
    fake_client = FakeClient([
        FakeResponse({"choices": [{"message": {"content": "ok"}}]}),
    ])
    monkeypatch.setattr("app.services.qwen_client.httpx.AsyncClient", lambda **kwargs: fake_client)

    result = await call_qwen_with_resilience(
        url="https://qwen.example.test",
        api_key="key",
        payload={"messages": []},
        circuit_breaker=CircuitBreaker(),
    )

    assert result == "ok"
    assert fake_client.posts[0][1]["Authorization"] == "Bearer key"


@pytest.mark.asyncio
async def test_call_qwen_retries_then_succeeds(monkeypatch):
    fake_client = FakeClient([
        httpx.TimeoutException("slow"),
        FakeResponse({"choices": [{"message": {"content": "after retry"}}]}),
    ])
    monkeypatch.setattr("app.services.qwen_client.httpx.AsyncClient", lambda **kwargs: fake_client)
    monkeypatch.setattr("app.services.qwen_client.asyncio.sleep", AsyncMock())

    result = await call_qwen_with_resilience(
        url="https://qwen.example.test",
        api_key="key",
        payload={"messages": []},
        backoff_base=0,
        circuit_breaker=CircuitBreaker(),
    )

    assert result == "after retry"
    assert len(fake_client.posts) == 2


@pytest.mark.asyncio
async def test_call_qwen_exhausts_retries(monkeypatch):
    fake_client = FakeClient([httpx.TimeoutException("slow")] * 3)
    monkeypatch.setattr("app.services.qwen_client.httpx.AsyncClient", lambda **kwargs: fake_client)
    monkeypatch.setattr("app.services.qwen_client.asyncio.sleep", AsyncMock())

    with pytest.raises(AdvisorProviderError, match="fall after 3 attempts"):
        await call_qwen_with_resilience(
            url="https://qwen.example.test",
            api_key="key",
            payload={"messages": []},
            max_attempts=3,
            backoff_base=0,
            circuit_breaker=CircuitBreaker(failure_threshold=99),
        )


@pytest.mark.asyncio
async def test_call_qwen_non_retryable_error_stops_immediately(monkeypatch):
    fake_client = FakeClient([_http_status_error(400)])
    monkeypatch.setattr("app.services.qwen_client.httpx.AsyncClient", lambda **kwargs: fake_client)

    with pytest.raises(AdvisorProviderError, match="Qwen return error"):
        await call_qwen_with_resilience(
            url="https://qwen.example.test",
            api_key="key",
            payload={"messages": []},
            circuit_breaker=CircuitBreaker(),
        )

    assert len(fake_client.posts) == 1


@pytest.mark.asyncio
async def test_call_qwen_raises_when_circuit_open(monkeypatch):
    fake_client = FakeClient([httpx.TimeoutException("slow")] * 5)
    monkeypatch.setattr("app.services.qwen_client.httpx.AsyncClient", lambda **kwargs: fake_client)
    monkeypatch.setattr("app.services.qwen_client.asyncio.sleep", AsyncMock())

    with pytest.raises(AdvisorCircuitOpenError):
        await call_qwen_with_resilience(
            url="https://qwen.example.test",
            api_key="key",
            payload={"messages": []},
            max_attempts=6,
            backoff_base=0,
            circuit_breaker=CircuitBreaker(failure_threshold=1, recovery_timeout=60),
        )
