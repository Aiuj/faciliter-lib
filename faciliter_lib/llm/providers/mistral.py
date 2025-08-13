from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from faciliter_lib.llm.core import ChatRequest, ChatResponse, LLMProvider, ProviderError, RateLimitError, TransientError, ToolCall, Usage, validate_with_schema
from faciliter_lib.tracing.logger import setup_logging

_log = setup_logging("faciliter_lib", __name__)


class MistralProvider:
    name = "mistral"

    def __init__(self) -> None:
        try:
            from mistralai import Mistral  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("mistralai package is required for MistralProvider") from e

    async def chat(self, req: ChatRequest) -> ChatResponse:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._chat_sync, req)

    def _chat_sync(self, req: ChatRequest) -> ChatResponse:
        from mistralai import Mistral, RateLimitError as MRate, APIError

        client = Mistral(api_key=req.extra.get("api_key") or os.getenv("MISTRAL_API_KEY"))
        messages = req.messages
        tools = None
        if req.tools:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.parameters or {"type": "object"},
                    },
                }
                for t in req.tools
            ]

        try:
            resp = client.chat.complete(
                model=req.model,
                messages=messages,
                tools=tools,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
            msg = resp.choices[0].message
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)

            tool_calls: List[ToolCall] = []
            tc_list = msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)
            if tc_list:
                for tc in tc_list:
                    if tc.get("type") == "function":
                        tool_calls.append(ToolCall(name=tc["function"]["name"], arguments=tc["function"].get("arguments", {})))

            usage = Usage(
                input_tokens=getattr(resp, "usage", {}).get("prompt_tokens", 0),
                output_tokens=getattr(resp, "usage", {}).get("completion_tokens", 0),
            )
            usage.total_tokens = usage.input_tokens + usage.output_tokens

            return ChatResponse(content=content, tool_calls=tool_calls, usage=usage, raw=resp)
        except MRate as e:
            raise RateLimitError(str(e))
        except APIError as e:
            raise TransientError(str(e))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(str(e))
