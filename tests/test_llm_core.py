import asyncio
import json
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock

from faciliter_lib.llm.core import LLMOrchestrator, ChatRequest, ChatResponse, Usage, ToolCall, RateLimiter, CircuitBreaker, ProviderError, RateLimitError


class DummyProvider:
    name = "dummy"

    def __init__(self):
        self.calls = 0

    async def chat(self, req: ChatRequest) -> ChatResponse:
        self.calls += 1
        if req.extra.get("fail_times") and self.calls <= req.extra["fail_times"]:
            raise RateLimitError("429")
        return ChatResponse(content="ok", usage=Usage(input_tokens=1, output_tokens=2))


@pytest.mark.asyncio
async def test_orchestrator_retry_and_success():
    prov = DummyProvider()
    orch = LLMOrchestrator(lambda name: prov)
    req = ChatRequest(provider="dummy", model="x", messages=[{"role": "user", "content": "hi"}], extra={"fail_times": 2})
    res = await orch.submit(req)
    assert res.content == "ok"
    assert prov.calls == 3


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    class FailingProvider(DummyProvider):
        async def chat(self, req: ChatRequest) -> ChatResponse:
            raise RateLimitError("429")

    prov = FailingProvider()
    orch = LLMOrchestrator(lambda name: prov, circuit_breaker=CircuitBreaker(failure_threshold=1, reset_seconds=1))
    req = ChatRequest(provider="dummy", model="m", messages=[{"role": "user", "content": "hi"}])

    with pytest.raises(RateLimitError):
        await orch.submit(req)

    with pytest.raises(ProviderError):
        await orch.submit(req)  # breaker open -> fast fail


@pytest.mark.asyncio
async def test_rate_limiter_applied():
    prov = DummyProvider()
    rate = RateLimiter()
    rate.configure(("dummy", "m"), rate_per_sec=1000)
    orch = LLMOrchestrator(lambda name: prov, rate_limiter=rate)
    req = ChatRequest(provider="dummy", model="m", messages=[{"role": "user", "content": "hi"}])
    res = await orch.submit(req)
    assert res.content == "ok"
