from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx



logger = logging.getLogger(__name__)


_PRIMARY_MODEL = "qwen-flash"
_FALLBACK_MODEL = "qwen-plus"

_MAX_ATTEMPTS = 6          
_FALLBACK_AFTER_ATTEMPT = 2  
_CIRCUIT_BREAKER_AFTER = 5   

_BACKOFF_BASE = 1.0        
_BACKOFF_MAX = 30.0       

#HTTP Code retryable  
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}



class _CircuitState(Enum):
    CLOSED = "closed"     
    OPEN = "open"           
    HALF_OPEN = "half_open" 

@dataclass
class CircuitBreaker:

    failure_threshold: int = 5
    recovery_timeout: float = 60.0

    _state: _CircuitState = field(default=_CircuitState.CLOSED, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: float | None = field(default=None, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def state(self) -> _CircuitState:
        return self._state

    async def allow_request(self) -> bool:
        async with self._lock:
            if self._state == _CircuitState.CLOSED:
                return True
            if self._state == _CircuitState.OPEN:
                if self._opened_at is not None and (time.monotonic() - self._opened_at) >= self.recovery_timeout:
                    self._state = _CircuitState.HALF_OPEN
                    logger.info("CircuitBreaker → HALF_OPEN ")
                    return True
                return False
            return True

    async def record_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            if self._state != _CircuitState.CLOSED:
                logger.info("CircuitBreaker → CLOSED ")
            self._state = _CircuitState.CLOSED
            self._opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            if self._state == _CircuitState.HALF_OPEN:
           
                self._state = _CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "CircuitBreaker → OPEN after failure in HALF_OPEN"
                    "(will retry after %.0fs)", self.recovery_timeout
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = _CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.error(
                    "CircuitBreaker → OPEN after %d failures"
                    "(will retry after %.0fs)",
                    self._failure_count, self.recovery_timeout,
                )


_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

def _backoff_seconds(attempt: int, base: float = _BACKOFF_BASE, cap: float = _BACKOFF_MAX) -> float:
    """Exponential backoff : wait = random(0, min(cap, base * 2^attempt))."""
    ceiling = min(cap, base * (2 ** attempt))
    return ceiling

def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS
    
    if isinstance(exc, httpx.NetworkError):
        return True
    return False


def _model_for_attempt(attempt: int) -> str:
    """select model based on attempt number: attempt 0-2 uses primary, then fallback."""
    if attempt <= _FALLBACK_AFTER_ATTEMPT:
        return _PRIMARY_MODEL
    return _FALLBACK_MODEL

async def _single_attempt(
    *,
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    model: str,
) -> str:
    """
    Try one API call to Qwen with the given model. Raises exceptions on failure.
    """
    attempt_payload = {**payload, "model": model}

    response = await client.post(url, headers=headers, json=attempt_payload)
    response.raise_for_status()

    data: dict[str, Any] = response.json()
    try:
        content: str = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Qwen response has invalid JSON structure: {data!r}") from exc

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Qwen response content is empty or not a string")

    return content.strip()


# Public API
async def call_qwen_with_resilience(
        
    
    
    *,
    url: str,
    api_key: str | None = None,
    payload: dict[str, Any],
    timeout: float = 30.0,
    max_attempts: int = _MAX_ATTEMPTS,
    backoff_base: float = _BACKOFF_BASE,
    circuit_breaker: CircuitBreaker = _circuit_breaker,
) -> str:
    """
    Gọi Qwen API với Retry + Fallback Model + Circuit Breaker.

    Parameters
    ----------
    url        : endpoint chat/completions đầy đủ.
    api_key    : DashScope API key.
    payload    : body request (KHÔNG bao gồm trường "model" – sẽ được inject tự động).
    timeout    : giây timeout mỗi request.
    max_attempts: tổng số lần thử tối đa (mặc định 6).
    backoff_base: hệ số cơ sở cho exponential backoff.
    circuit_breaker: instance CircuitBreaker dùng chung.

    Returns
    -------
    str : nội dung câu trả lời từ model.

    Raises
    ------
    AdvisorCircuitOpenError  : nếu CB đang OPEN và không phục hồi được.
    AdvisorProviderError     : nếu đã hết số lần thử.
    """

    from app.services.advisor import AdvisorConfigurationError
    resolved_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not resolved_key:
        raise AdvisorConfigurationError("DASHSCOPE_API_KEY is missing")
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
    }
    last_exc: Exception | None = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_attempts):

            if attempt >= _CIRCUIT_BREAKER_AFTER:
                if not await circuit_breaker.allow_request():
                    raise AdvisorCircuitOpenError(
                        f"Circuit Breaker OPEN. "
                        f"retry after {circuit_breaker.recovery_timeout:.0f}s. "
                        f"(attempt={attempt})"
                    )

            model = _model_for_attempt(attempt)
            log_prefix = f"[attempt={attempt}, model={model}]"

            if attempt > 0:
                wait = _backoff_seconds(attempt, base=backoff_base)
                logger.info("%s  backoff %.2fs before retry…", log_prefix, wait)
                await asyncio.sleep(wait)

                #change model fallback
                if attempt == _FALLBACK_AFTER_ATTEMPT + 1:
                    logger.warning(
                        "%s qwen-flash failed %d times → change qwen-plus",
                        log_prefix, _FALLBACK_AFTER_ATTEMPT + 1,
                    )

            # Bước 3: Call APi 
            try:
                logger.debug("%s  request…", log_prefix)
                result = await _single_attempt(
                    client=client,
                    url=url,
                    headers=headers,
                    payload=payload,
                    model=model,
                )
                # Thành công → reset CB
                await circuit_breaker.record_success()
                logger.info("%s ✓ Complete", log_prefix)
                return result

            except Exception as exc:
                last_exc = exc
                await circuit_breaker.record_failure()

                if _is_retryable(exc):
                    status = (
                        exc.response.status_code
                        if isinstance(exc, httpx.HTTPStatusError)
                        else "timeout/network"
                    )
                    logger.warning(
                        "%s error retryable (%s): %s — sẽ retry",
                        log_prefix, status, exc,
                    )
                else:
                   
                    logger.error(
                        "%s not retryable: %s", log_prefix, exc
                    )
                    raise AdvisorProviderError(
                        f"Qwen return error: {exc}"
                    ) from exc

    raise AdvisorProviderError(
        f"Qwen fall after {max_attempts} attempts. Last error: {last_exc}"
    ) from last_exc


class AdvisorProviderError(RuntimeError):
    """Raised when Qwen API call fails after exhausting all retries."""


class AdvisorCircuitOpenError(AdvisorProviderError):
    """Raised when Circuit Breaker is OPEN, blocking requests immediately."""
