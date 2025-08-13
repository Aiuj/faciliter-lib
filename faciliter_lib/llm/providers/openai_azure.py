from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from faciliter_lib.llm.core import ChatRequest, ChatResponse, LLMProvider, ProviderError, RateLimitError, TransientError, ToolCall, Usage, validate_with_schema
from faciliter_lib.tracing.logger import setup_logging

_log = setup_logging("faciliter_lib", __name__)


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("openai package >=1.0 is required for OpenAIProvider") from e
        self._OpenAI = OpenAI

    async def chat(self, req: ChatRequest) -> ChatResponse:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._chat_sync, req)

    def _chat_sync(self, req: ChatRequest) -> ChatResponse:
        from openai import APIConnectionError, RateLimitError as OAIRate, InternalServerError, BadRequestError
        from openai import OpenAI

        client = OpenAI(
            api_key=req.extra.get("api_key") or os.getenv("OPENAI_API_KEY"),
            base_url=req.extra.get("base_url") or os.getenv("OPENAI_BASE_URL"),
        )

        messages: List[Dict[str, Any]] = []
        if req.system_message:
            messages.append({"role": "system", "content": req.system_message})
        messages.extend(req.messages)

        tools = None
        tool_choice = None
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
            if req.use_tool_calling_for_structured and req.json_schema:
                # Suggest tool with schema
                tool_choice = "auto"

        response_format: Optional[Dict[str, Any]] = None
        if req.json_schema and not req.use_tool_calling_for_structured:
            response_format = {"type": "json_schema", "json_schema": {"schema": req.json_schema}}

        try:
            completion = client.chat.completions.create(
                model=req.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                response_format=response_format,
                idempotency_key=req.idempotency_key,
            )

            choice = completion.choices[0]
            content = choice.message.content

            tool_calls: List[ToolCall] = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    if getattr(tc, "type", "function") == "function":
                        tool_calls.append(
                            ToolCall(name=tc.function.name, arguments=tc.function.arguments or {})
                        )

            structured = None
            if response_format and content:
                import json

                structured = validate_with_schema(json.loads(content), req.json_schema or {})

            usage = Usage(
                input_tokens=getattr(completion, "usage", {}).get("prompt_tokens", 0),
                output_tokens=getattr(completion, "usage", {}).get("completion_tokens", 0),
            )
            usage.total_tokens = usage.input_tokens + usage.output_tokens

            return ChatResponse(
                content=content,
                structured=structured,
                tool_calls=tool_calls,
                usage=usage,
                raw=completion,
            )
        except OAIRate as e:
            raise RateLimitError(str(e))
        except (APIConnectionError, InternalServerError) as e:
            raise TransientError(str(e))
        except BadRequestError as e:
            raise ProviderError(str(e))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(str(e))
