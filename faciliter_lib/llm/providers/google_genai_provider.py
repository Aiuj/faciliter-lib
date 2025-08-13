"""Google GenAI provider using the official google.genai SDK.

Docs consulted via Context7 show structured outputs with Pydantic are supported
by passing response_mime_type='application/json' and response_schema=MyModel to
GenerateContentConfig, and chat via client.chats.create(...).send_message(...).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .base import BaseProvider
from ..llm_config import GeminiConfig
from faciliter_lib import get_module_logger
from faciliter_lib.tracing.tracing import add_trace_metadata

logger = get_module_logger()

class GoogleGenAIProvider(BaseProvider):
    """Provider implementation for Google GenAI (Gemini)."""

    def __init__(self, config: GeminiConfig) -> None:  # type: ignore[override]
        super().__init__(config)

        # Lazy import to avoid hard dependency if unused
        from google import genai  # type: ignore

        # Build client; supports API key from env or passed explicitly
        # Gemini Developer API (default). Vertex AI could be added later.
        self._client = genai.Client(api_key=config.api_key)

        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        GoogleGenAIInstrumentor().instrument()

    def _to_genai_messages(self, messages: List[Dict[str, str]]) -> str:
        """Flatten OpenAI-style messages to a single prompt string.

        google.genai chat API supports chat sessions, but mapping roles to a
        single prompt keeps things simple for now. For richer role handling,
        we could use client.chats and turn history, but generate_content also
        accepts contents=str. We'll join messages into a single text.
        """
        parts: List[str] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role in ("assistant", "ai"):
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")
        return "\n".join(parts)

    def _build_config(
        self,
        *,
        structured_output: Optional[Type[BaseModel]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_message: Optional[str] = None,
        use_search_grounding: bool = False,
        thinking_enabled_override: Optional[bool] = None,
    ) -> Dict[str, Any]:
        from google.genai import types  # type: ignore

        cfg: Dict[str, Any] = {
            "temperature": self.config.temperature,
        }
        if getattr(self.config, "max_tokens", None) is not None:
            cfg["max_output_tokens"] = self.config.max_tokens

        # Thinking configuration (Gemini 2.5 series)
        try:
            model_lc = (self.config.model or "").lower()
            supports_thinking = "2.5" in model_lc
            # precedence: chat override > config
            enabled = thinking_enabled_override
            if enabled is None:
                enabled = getattr(self.config, "thinking_enabled", False)
            if supports_thinking:
                if enabled:
                    # Include thoughts in output
                    cfg["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
                else:
                    # Disable thinking to reduce latency when allowed (not on pro)
                    if "pro" not in model_lc:
                        cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except Exception:
            # Never fail building config due to thinking support
            pass

        if system_message:
            cfg["system_instruction"] = system_message

        if tools:
            cfg["tools"] = tools

        # Grounding via Google Search (per official docs)
        # https://ai.google.dev/gemini-api/docs/google-search
        # This uses safety-reviewed search augmentation when supported by the model.
        if use_search_grounding:
            try:
                # Enable Google Search tool and config per official docs
                gs = types.GoogleSearch()
                gs_tool = types.Tool(google_search=gs)
                if cfg.get("tools"):
                    cfg["tools"] = [*cfg["tools"], gs_tool]
                else:
                    cfg["tools"] = [gs_tool]
                cfg["tool_config"] = types.ToolConfig(google_search=gs)
            except Exception:
                # Fail-soft: if SDK/version doesn't support it, ignore silently
                pass

        if structured_output is not None:
            # Use official structured output support
            cfg = {
                **cfg,
                "response_mime_type": "application/json",
                "response_schema": structured_output,
            }
        return {"config": types.GenerateContentConfig(**cfg)}

    def _build_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        # google.genai supports tools and tool_config; for now pass through as-is
        # when in OpenAI function-call schema. Advanced conversion could be added.
        if not tools:
            return {}
        return {"tools": tools}

    def chat(
        self,
        *,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None,
        use_search_grounding: bool = False,
        thinking_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        try:
            # Minimal debug without leaking content
            logger.debug(
                "genai.chat start",
                extra={
                    "llm_provider": "gemini",
                    "model": self.config.model,
                    "msg_count": len(messages),
                    "has_tools": bool(tools),
                    "structured": bool(structured_output),
                },
            )
            # Determine if this is a single-turn prompt (only one user message, optional system)
            user_messages = [m for m in messages if m.get("role") == "user"]
            assistant_messages = [m for m in messages if m.get("role") == "assistant"]
            is_single_turn = len(user_messages) == 1 and len(assistant_messages) == 0 and len(messages) <= 2

            if is_single_turn:
                user_text = user_messages[0].get("content", "")
                extra = self._build_config(
                    structured_output=structured_output,
                    tools=tools,
                    system_message=system_message,
                    use_search_grounding=use_search_grounding,
                    thinking_enabled_override=thinking_enabled,
                )
                resp = self._client.models.generate_content(
                    model=self.config.model,
                    contents=user_text,
                    **extra,
                )
            else:
                prompt = self._to_genai_messages(messages)
                extra = self._build_config(
                    structured_output=structured_output,
                    tools=tools,
                    system_message=system_message,
                    use_search_grounding=use_search_grounding,
                    thinking_enabled_override=thinking_enabled,
                )
                # Preserve multi-turn via chats API
                chat = self._client.chats.create(model=self.config.model)
                resp = chat.send_message(prompt, **extra)  # type: ignore[arg-type]

            tool_calls: List[Dict[str, Any]] = []
            usage = getattr(resp, "usage_metadata", {}) or {}

            if getattr(resp, "function_calls", None):
                for fc in resp.function_calls:  # type: ignore[attr-defined]
                    tool_calls.append(
                        {
                            "id": fc.get("id") if isinstance(fc, dict) else None,
                            "function": {
                                "name": fc.get("name") if isinstance(fc, dict) else getattr(fc, "name", ""),
                                "arguments": fc.get("args") if isinstance(fc, dict) else getattr(fc, "args", {}),
                            },
                            "type": "function",
                        }
                    )

            # Attach minimal metadata to current trace (provider-agnostic)
            try:
                add_trace_metadata(
                    {
                        "llm_provider": "google-gemini",
                        "model": self.config.model,
                        "structured": bool(structured_output),
                        "has_tools": bool(tools),
                        "single_turn": is_single_turn,
                        "usage": getattr(resp, "usage_metadata", {}) or {},
                    }
                )
            except Exception:
                # Tracing metadata should never break the call
                pass

            if structured_output is not None:
                # Prefer SDK-native parsed output, but ensure the return value is JSON-serializable
                # to avoid recursion/serialization issues in callers.
                content: Any
                raw_text: str = getattr(resp, "text", "")
                parsed = getattr(resp, "parsed", None)
                if parsed is not None:
                    if isinstance(parsed, BaseModel):
                        content = parsed.model_dump()
                    else:
                        content = parsed
                else:
                    # Fallback for older SDKs: validate from JSON text to a BaseModel, then dump to dict
                    text = raw_text
                    try:
                        data = structured_output.model_validate_json(text)  # type: ignore[attr-defined]
                        content = data.model_dump()
                    except Exception:
                        import json as _json

                        content = _json.loads(text) if text else {}
                # Also return text and content_json for convenience
                import json as _json
                return {
                    "content": content,
                    "structured": True,
                    "tool_calls": tool_calls,
                    "usage": usage,
                    "text": raw_text,
                    "content_json": _json.dumps(content, ensure_ascii=False),
                }

            # Plain text chat
            return {
                "content": getattr(resp, "text", ""),
                "structured": False,
                "tool_calls": tool_calls,
                "usage": usage,
            }
        except Exception as e:  # pragma: no cover - network errors
            logger.exception("genai.chat failed")
            return {
                "error": str(e),
                "content": None,
                "structured": structured_output is not None,
                "tool_calls": [],
                "usage": {},
            }
