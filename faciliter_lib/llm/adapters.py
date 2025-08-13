from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from faciliter_lib.llm.core import ChatRequest, LLMOrchestrator
from faciliter_lib.llm import llm_client as _llm_client_module


class LangChainChatAdapter:  # Lightweight BaseChatModel shim (no hard dep)
    def __init__(self, provider: str, model: str, temperature: float = 0.7, max_tokens: Optional[int] = None):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # pick up patched factory dynamically from llm_client module
        self._orch = LLMOrchestrator(_llm_client_module._provider_factory)

    def invoke(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        req = ChatRequest(provider=self.provider, model=self.model, messages=messages, temperature=self.temperature, max_tokens=self.max_tokens)

        async def _run():
            res = await self._orch.submit(req)
            return {"content": res.content, "tool_calls": [
                {"type": "function", "function": {"name": tc.name, "arguments": tc.arguments}} for tc in res.tool_calls
            ], "usage": res.usage.__dict__}

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run_coroutine_threadsafe(_run(), loop).result()
        return asyncio.run(_run())


class LlamaIndexCustomLLM:  # Minimal CustomLLM shim
    def __init__(self, provider: str, model: str, temperature: float = 0.7, max_tokens: Optional[int] = None):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._orch = LLMOrchestrator(_llm_client_module._provider_factory)

    def complete(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        req = ChatRequest(provider=self.provider, model=self.model, messages=messages, temperature=self.temperature, max_tokens=self.max_tokens)

        async def _run():
            res = await self._orch.submit(req)
            return res.content or ""

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return asyncio.run_coroutine_threadsafe(_run(), loop).result()
        return asyncio.run(_run())
