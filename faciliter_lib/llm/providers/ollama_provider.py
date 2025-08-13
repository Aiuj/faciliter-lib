"""Ollama provider using the official ollama Python library.

Supports native tools (function calling) and simple structured outputs via
format='json'.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .base import BaseProvider
from ..llm_config import OllamaConfig
from faciliter_lib import get_module_logger

logger = get_module_logger()


class OllamaProvider(BaseProvider):
    """Provider implementation for Ollama (local models)."""

    def __init__(self, config: OllamaConfig) -> None:  # type: ignore[override]
        super().__init__(config)
        import ollama  # type: ignore

        self._ollama = ollama

    def _build_options(self) -> Dict[str, Any]:
        # Map config to ollama options when available
        options: Dict[str, Any] = {
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            options["num_predict"] = self.config.max_tokens
        if self.config.num_ctx is not None:
            options["num_ctx"] = self.config.num_ctx
        if self.config.num_predict is not None:
            options["num_predict"] = self.config.num_predict
        if self.config.repeat_penalty is not None:
            options["repeat_penalty"] = self.config.repeat_penalty
        if self.config.top_k is not None:
            options["top_k"] = self.config.top_k
        if self.config.top_p is not None:
            options["top_p"] = self.config.top_p
        return options

    def chat(
        self,
        *,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None,
        use_search_grounding: bool = False,
    ) -> Dict[str, Any]:
        try:
            logger.debug(
                "ollama.chat start",
                extra={
                    "llm_provider": "ollama",
                    "model": self.config.model,
                    "msg_count": len(messages),
                    "has_tools": bool(tools),
                    "structured": bool(structured_output),
                    "search_grounding": use_search_grounding,
                },
            )
            payload: Dict[str, Any] = {
                "model": self.config.model,
                "messages": messages,
                "options": self._build_options(),
            }
            if tools:
                payload["tools"] = tools

            resp_format: Optional[str] = None
            if structured_output is not None:
                # Ollama supports format='json'. We'll validate with Pydantic if provided.
                resp_format = "json"
                payload["format"] = structured_output.model_json_schema()

            # Configure host via custom client if base_url differs
            if getattr(self.config, "base_url", None):
                from ollama import Client  # type: ignore

                client = Client(host=self.config.base_url)
                resp = client.chat(**payload)
            else:
                resp = self._ollama.chat(**payload)

            message = resp.get("message", {})
            content_text = message.get("content", "")
            tool_calls = message.get("tool_calls", []) or []
            usage = resp.get("usage", {}) or {}

            # If structured_output requested, attempt to validate
            if resp_format is not None and structured_output is not None:
                try:
                    data = structured_output.model_validate_json(content_text)  # type: ignore[attr-defined]
                    content: Any = data.model_dump()
                except Exception:
                    import json as _json

                    try:
                        content = _json.loads(content_text) if content_text else {}
                    except Exception:
                        content = {"_raw": content_text}
                import json as _json
                return {
                    "content": content,
                    "structured": True,
                    "tool_calls": tool_calls or [],
                    "usage": usage,
                    "text": content_text,
                    "content_json": _json.dumps(content, ensure_ascii=False),
                }

            return {
                "content": content_text,
                "structured": False,
                "tool_calls": tool_calls,
                "usage": usage,
            }
        except Exception as e:  # pragma: no cover - runtime connectivity
            logger.exception("ollama.chat failed")
            return {
                "error": str(e),
                "content": None,
                "structured": structured_output is not None,
                "tool_calls": [],
                "usage": {},
            }
