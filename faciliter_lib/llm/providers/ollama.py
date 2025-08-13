from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from faciliter_lib.llm.core import ChatRequest, ChatResponse, LLMProvider, ProviderError, RateLimitError, TransientError, ToolCall, Usage
from faciliter_lib.tracing.logger import setup_logging

_log = setup_logging("faciliter_lib", __name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        try:
            import ollama  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("ollama package is required for OllamaProvider") from e

    async def chat(self, req: ChatRequest) -> ChatResponse:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._chat_sync, req)

    def _chat_sync(self, req: ChatRequest) -> ChatResponse:
        import ollama

        try:
            options = {}
            if req.temperature is not None:
                options["temperature"] = req.temperature
            if req.max_tokens is not None:
                options["num_predict"] = req.max_tokens

            # Format tools for Ollama if available
            # Note: Ollama's tool support varies; we default to plain prompt
            messages = req.messages

            res = ollama.chat(
                model=req.model,
                messages=messages,
                options=options or None,
            )
            msg = (res.get("message") or {}) if isinstance(res, dict) else getattr(res, "message", {})
            content = msg.get("content") if isinstance(msg, dict) else None

            # No standardized usage in ollama python yet
            usage = Usage()
            return ChatResponse(content=content, usage=usage, raw=res)
        except ollama.ResponseError as e:  # type: ignore
            # Map 429 to RateLimitError when possible
            if getattr(e, "status_code", None) == 429:
                raise RateLimitError(str(e))
            raise ProviderError(str(e))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(str(e))
