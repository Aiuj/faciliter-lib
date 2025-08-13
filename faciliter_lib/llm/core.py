"""Provider-agnostic LLM core: request/response types, orchestrator with retries,
rate limiting, backpressure, and tracing hooks.

This module forms the tiny, shared kernel. Providers are implemented in
faciliter_lib.llm.providers.* and plugged into the orchestrator.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple, Union

from jsonschema import Draft202012Validator, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_fixed,
    retry_if_exception,
    RetryCallState,
)
try:
    from aiolimiter import AsyncLimiter  # type: ignore
except Exception:  # pragma: no cover - fallback when aiolimiter isn't installed
    class AsyncLimiter:  # Minimal shim
        def __init__(self, max_rate: float, time_period: float = 1) -> None:
            self._sema = asyncio.Semaphore(int(max(1, max_rate)))

        async def __aenter__(self):  # noqa: D401
            await self._sema.acquire()
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: D401
            self._sema.release()
            return False

from faciliter_lib.tracing.tracing import TracingManager
from faciliter_lib.tracing.logger import setup_logging


# Logger
_log = setup_logging("faciliter_lib", __name__)


# -------- Data shapes


Message = Dict[str, Any]  # {role: user|assistant|system|tool, content: str|list, ...}


@dataclass
class ToolSpec:
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None  # JSON Schema
    handler: Optional[Callable[..., Any]] = None  # Server-side callable (optional)


@dataclass
class ChatRequest:
    provider: str
    model: str
    messages: List[Message]
    tools: Optional[List[ToolSpec]] = None
    json_schema: Optional[Dict[str, Any]] = None  # Preferred structured mode
    use_tool_calling_for_structured: bool = False  # Fallback structured mode
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    system_message: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResponse:
    content: Optional[str]
    structured: Optional[Any] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    raw: Optional[Any] = None


# -------- Provider interface


class ProviderError(Exception):
    """Generic provider error."""


class RateLimitError(ProviderError):
    """Raised when provider returns a rate limit condition (429)."""


class TransientError(ProviderError):
    """Raised for transient server/network errors eligible for retry."""


class LLMProvider(Protocol):
    name: str

    async def chat(self, req: ChatRequest) -> ChatResponse:
        ...


# -------- Tool registry


class ToolRegistry:
    """Simple registry for server-executed tools with JSON Schema."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list(self) -> List[ToolSpec]:
        return list(self._tools.values())


# -------- Rate limiting per (provider, model)


class RateLimiter:
    def __init__(self) -> None:
        # key: (provider, model) -> AsyncLimiter(req/s)
        self._limiters: Dict[Tuple[str, str], AsyncLimiter] = {}
        # Optional global limiter
        self._global: Optional[AsyncLimiter] = None

    def configure(self, key: Tuple[str, str], rate_per_sec: float) -> None:
        self._limiters[key] = AsyncLimiter(max_rate=rate_per_sec, time_period=1)

    def configure_global(self, rate_per_sec: float) -> None:
        self._global = AsyncLimiter(max_rate=rate_per_sec, time_period=1)

    def limiter_for(self, provider: str, model: str) -> Optional[AsyncLimiter]:
        return self._limiters.get((provider, model))

    def global_limiter(self) -> Optional[AsyncLimiter]:
        return self._global


# -------- Circuit breaker


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_seconds: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failures: Dict[Tuple[str, str], int] = {}
        self._opened_until: Dict[Tuple[str, str], float] = {}

    def is_open(self, provider: str, model: str) -> bool:
        key = (provider, model)
        until = self._opened_until.get(key)
        if until and until > time.time():
            return True
        if until and until <= time.time():
            # Reset breaker after timeout
            self._opened_until.pop(key, None)
            self._failures.pop(key, None)
        return False

    def record_success(self, provider: str, model: str) -> None:
        self._failures[(provider, model)] = 0

    def record_failure(self, provider: str, model: str) -> None:
        key = (provider, model)
        self._failures[key] = self._failures.get(key, 0) + 1
        if self._failures[key] >= self.failure_threshold:
            self._opened_until[key] = time.time() + self.reset_seconds


# -------- Orchestrator


class LLMOrchestrator:
    """Coordinates retries, rate limits, queueing, circuit breaker, and tracing."""

    def __init__(
        self,
        provider_factory: Callable[[str], LLMProvider],
        rate_limiter: Optional[RateLimiter] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        max_concurrency_per_model: int = 8,
        tracing: Optional[TracingManager] = None,
    ) -> None:
        self._provider_factory = provider_factory
        self._rate = rate_limiter or RateLimiter()
        self._breaker = circuit_breaker or CircuitBreaker()
        self._queues: Dict[Tuple[str, str], asyncio.Queue[Tuple[ChatRequest, asyncio.Future]]] = {}
        self._semaphores: Dict[Tuple[str, str], asyncio.Semaphore] = {}
        self._max_concurrency = max_concurrency_per_model
        self._tracing = tracing or TracingManager("faciliter-lib")
        self._tracing.setup()

    def _get_queue(self, provider: str, model: str) -> asyncio.Queue:
        key = (provider, model)
        if key not in self._queues:
            self._queues[key] = asyncio.Queue(maxsize=100)
            # Start a background worker for this model
            asyncio.create_task(self._worker(provider, model))
        return self._queues[key]

    def _get_sema(self, provider: str, model: str) -> asyncio.Semaphore:
        key = (provider, model)
        if key not in self._semaphores:
            self._semaphores[key] = asyncio.Semaphore(self._max_concurrency)
        return self._semaphores[key]

    async def _worker(self, provider: str, model: str) -> None:
        queue = self._get_queue(provider, model)
        while True:
            req, fut = await queue.get()
            try:
                res = await self._execute(req)
                if not fut.cancelled():
                    fut.set_result(res)
            except Exception as e:  # noqa: BLE001
                if not fut.cancelled():
                    fut.set_exception(e)
            finally:
                queue.task_done()

    async def submit(self, req: ChatRequest) -> ChatResponse:
        if self._breaker.is_open(req.provider, req.model):
            raise ProviderError(
                f"Circuit breaker open for {req.provider}:{req.model}; failing fast"
            )
        queue = self._get_queue(req.provider, req.model)
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        await queue.put((req, fut))
        return await fut

    # Retry policy
    def _retry_predicate(self, exc: BaseException) -> bool:
        return isinstance(exc, (RateLimitError, TransientError, asyncio.TimeoutError))

    async def _execute(self, req: ChatRequest) -> ChatResponse:
        provider = self._provider_factory(req.provider)
        limiter = self._rate.limiter_for(req.provider, req.model)
        global_limiter = self._rate.global_limiter()
        sema = self._get_sema(req.provider, req.model)

        from tenacity import AsyncRetrying

        # Fast retries during tests: when running under pytest or explicitly requested
        test_fast = bool(os.getenv("PYTEST_CURRENT_TEST")) or bool(req.extra.get("test_fast"))
        wait_strategy = wait_fixed(0) if test_fast else wait_exponential_jitter(initial=0.5, max=8.0)

        def _before_sleep_cb(retry_state: RetryCallState) -> None:
            # Record failure to the circuit breaker and log
            try:
                self._breaker.record_failure(req.provider, req.model)
            except Exception:  # pragma: no cover - defensive
                pass
            self._before_sleep(retry_state)

        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(5),
            wait=wait_strategy,
            retry=retry_if_exception(self._retry_predicate),
            before_sleep=_before_sleep_cb,
        ):
            with attempt:
                async with sema:
                    if global_limiter:
                        async with global_limiter:
                            if limiter:
                                async with limiter:
                                    res = await provider.chat(req)
                                    self._breaker.record_success(req.provider, req.model)
                                    return res
                            res = await provider.chat(req)
                            self._breaker.record_success(req.provider, req.model)
                            return res
                    if limiter:
                        async with limiter:
                            res = await provider.chat(req)
                            self._breaker.record_success(req.provider, req.model)
                            return res
                    res = await provider.chat(req)
                    self._breaker.record_success(req.provider, req.model)
                    return res

        raise ProviderError("Unexpected retry termination")

    def _before_sleep(self, retry_state: RetryCallState) -> None:
        # Add jitter/backoff info to logs
        _log.warning(
            f"Retrying LLM call after error: {retry_state.outcome.exception() if retry_state.outcome else 'unknown'}"
        )


# -------- Structured output helpers


def validate_with_schema(data: Any, schema: Dict[str, Any]) -> Any:
    try:
        Draft202012Validator(schema).validate(data)
        return data
    except ValidationError as e:  # pragma: no cover (edge detail)
        raise ProviderError(f"Structured output failed schema validation: {e.message}")
