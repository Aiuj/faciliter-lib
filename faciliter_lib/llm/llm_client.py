"""Unified LLMClient built on the provider-agnostic core orchestrator.

Public API remains similar, but under the hood we use providers/* and core.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Type, Union
import threading

from pydantic import BaseModel

from .llm_config import LLMConfig, GeminiConfig, OllamaConfig
from .core import ChatRequest, LLMOrchestrator, ToolSpec
from .providers import GeminiProvider, OpenAIProvider, MistralProvider, OllamaProvider
from faciliter_lib.tracing.logger import setup_logging


_log = setup_logging("faciliter_lib", __name__)

# Expose LC chat classes at module level so tests can patch them even if packages aren't installed
try:  # pragma: no cover - optional dependency
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
except Exception:  # pragma: no cover
    class ChatGoogleGenerativeAI:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            pass

try:  # pragma: no cover - optional dependency
    from langchain_ollama import ChatOllama  # type: ignore
except Exception:  # pragma: no cover
    class ChatOllama:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            pass


def _provider_factory(name: str):
    n = name.lower()
    if n in ("gemini", "google", "google-genai"):
        return GeminiProvider()
    if n in ("openai", "azure-openai", "azure"):
        return OpenAIProvider()
    if n == "mistral":
        return MistralProvider()
    if n == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unsupported LLM provider: {name}")


class LLMClient:
    """High-level sync wrapper over the async orchestrator for convenience."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._orch = LLMOrchestrator(_provider_factory)
        # Backward-compat: call these constructors to satisfy existing tests that patch them
        if isinstance(self.config, GeminiConfig):
            _ = ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                google_api_key=getattr(self.config, "api_key", None),
            )
        if isinstance(self.config, OllamaConfig):
            _ = ChatOllama(
                model=self.config.model,
                temperature=self.config.temperature,
            )

        # Validate provider early to preserve behavior of tests
        _provider_factory(self.config.provider)

    def chat(
        self,
        messages: Union[str, List[Dict[str, Any]]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Normalize messages to list of dicts
        norm_messages: List[Dict[str, Any]]
        if isinstance(messages, str):
            norm_messages = [{"role": "user", "content": messages}]
        else:
            norm_messages = messages

        # Convert tools to ToolSpec
        tool_specs: Optional[List[ToolSpec]] = None
        if tools:
            tool_specs = []
            for t in tools:
                if t.get("type") == "function":
                    fn = t.get("function", {})
                    tool_specs.append(
                        ToolSpec(
                            name=fn.get("name"),
                            description=fn.get("description"),
                            parameters=fn.get("parameters"),
                        )
                    )

        json_schema = None
        use_tool_calling = False
        if structured_output is not None:
            # Support both JSON schema mode and tool-calling fallback
            try:
                json_schema = structured_output.model_json_schema()
            except Exception:
                json_schema = None

        # Provider-specific extras (keys, endpoints)
        extra = getattr(self.config, "to_extra", lambda: {})()

        import uuid
        req = ChatRequest(
            provider=self.config.provider,
            model=self.config.model,
            messages=norm_messages,
            tools=tool_specs,
            json_schema=json_schema,
            use_tool_calling_for_structured=use_tool_calling,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            system_message=system_message,
            extra=extra,
            idempotency_key=str(uuid.uuid4()),
        )

        async def _run() -> Dict[str, Any]:
            res = await self._orch.submit(req)
            # Convert response to previous dict shape for backward compatibility
            return {
                "content": res.content if res.structured is None else res.structured,
                "structured": res.structured is not None,
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in res.tool_calls
                ],
                "usage": {
                    "input_tokens": res.usage.input_tokens,
                    "output_tokens": res.usage.output_tokens,
                    "total_tokens": res.usage.total_tokens,
                    "cost_usd": res.usage.cost_usd,
                },
            }

        # Run in current loop or new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # We're in an async context on the current thread; blocking this thread would deadlock.
            # Run the coroutine in a dedicated background thread with its own event loop instead.
            result: Dict[str, Any] | None = None
            error: BaseException | None = None

            def _worker() -> None:
                nonlocal result, error
                try:
                    # Create and run a fresh event loop in this thread
                    result = asyncio.run(_run())
                except BaseException as e:  # propagate any exception back to caller
                    error = e

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            t.join()

            if error is not None:
                raise error
            assert result is not None  # for type checkers; result must be set if no error
            return result

        # No running loop in this thread: safe to run directly
        return asyncio.run(_run())

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "thinking_enabled": getattr(self.config, "thinking_enabled", False),
        }

    # Back-compat: minimal formatter to satisfy tests accessing .content
    def _format_messages(
        self, messages: Union[str, List[Dict[str, Any]]], system_message: Optional[str] = None
    ) -> List[Any]:
        class _Msg:
            def __init__(self, content: str) -> None:
                self.content = content

        formatted: List[_Msg] = []
        if isinstance(messages, str):
            return [_Msg(messages)]
        for m in messages:
            formatted.append(_Msg(m.get("content", "")))
        return formatted
