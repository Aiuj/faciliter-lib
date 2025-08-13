from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

from faciliter_lib.llm.core import ChatRequest, ChatResponse, LLMProvider, ProviderError, RateLimitError, TransientError, ToolCall, Usage, validate_with_schema
from faciliter_lib.tracing.logger import setup_logging

from faciliter_lib.tracing.tracing import setup_tracing

try:
    from google.genai import errors as genai_errors
except ImportError:
    genai_errors = None

_log = setup_logging("faciliter_lib", __name__)


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        try:
            from google import genai  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("google-genai package is required for GeminiProvider") from e
        self._genai = genai
        # Initialize tracing (no-op if not configured)
        try:
            self._tracing = setup_tracing()
        except Exception:  # pragma: no cover - defensive
            self._tracing = None

    async def chat(self, req: ChatRequest) -> ChatResponse:
        # google-genai client is sync; run in thread to avoid blocking
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._chat_sync, req)

    def _chat_sync(self, req: ChatRequest) -> ChatResponse:
        from google import genai  # type: ignore
        try:
            start = time.time()
            client = genai.Client(api_key=req.extra.get("api_key"))
            # Configure model
            generation_config = {
                "temperature": req.temperature,
                "max_output_tokens": req.max_tokens,
            }
            # Embedded search tool if requested
            tools = None
            if req.extra.get("enable_grounding"):
                tools = [genai.types.Tool(google_search=genai.types.GoogleSearch())]

            # Messages: convert to parts
            contents: List[Any] = []
            for m in req.messages:
                role = m.get("role", "user")
                contents.append({"role": "user" if role == "user" else role, "parts": [m.get("content", "")]})

            # JSON schema / tool calling preference
            response_mime_type = None
            if req.json_schema and not req.use_tool_calling_for_structured:
                response_mime_type = "application/json"
                generation_config["response_mime_type"] = response_mime_type
                generation_config["response_schema"] = req.json_schema

            # Trace request metadata (redacted/preview content)
            try:
                if getattr(self, "_tracing", None):
                    last_user = next((m for m in reversed(req.messages) if m.get("role") == "user"), None)
                    preview = (last_user or {}).get("content")
                    if isinstance(preview, str) and len(preview) > 200:
                        preview = preview[:200] + "..."
                    self._tracing.add_metadata({
                        "event": "llm.request",
                        "provider": self.name,
                        "model": req.model,
                        "temperature": req.temperature,
                        "max_tokens": req.max_tokens,
                        "has_json_schema": bool(req.json_schema),
                        "tools_count": len(req.tools or []),
                        "user_prompt_preview": preview,
                        "idempotency_key": req.idempotency_key,
                    })
            except Exception:
                pass

            config = genai.types.GenerateContentConfig(
                tools=tools,
                **{k: v for k, v in generation_config.items() if v is not None}
            )
            result = client.models.generate_content(
                model=req.model,
                contents=contents,
                config=config,
            )

            usage = Usage(
                input_tokens=getattr(result, "usage_metadata", {}).get("prompt_token_count", 0),
                output_tokens=getattr(result, "usage_metadata", {}).get("candidates_token_count", 0),
            )
            usage.total_tokens = usage.input_tokens + usage.output_tokens

            text = result.text if hasattr(result, "text") else None
            structured = None
            if response_mime_type == "application/json" and text:
                import json
                structured = validate_with_schema(json.loads(text), req.json_schema or {})

            # Gemini tool calls are delivered differently; we focus on content
            resp = ChatResponse(content=text, structured=structured, usage=usage, raw=result)

            # Trace response metadata
            try:
                if getattr(self, "_tracing", None):
                    latency_ms = int((time.time() - start) * 1000)
                    preview_out = text[:200] + "..." if isinstance(text, str) and len(text) > 200 else text
                    self._tracing.add_metadata({
                        "event": "llm.response",
                        "provider": self.name,
                        "model": req.model,
                        "latency_ms": latency_ms,
                        "usage": {
                            "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens,
                            "total_tokens": usage.total_tokens,
                        },
                        "structured": bool(structured is not None),
                        "text_preview": preview_out,
                    })
            except Exception:
                pass

            return resp
        except genai_errors.APIError as e:
            # Check for rate limit (429), blocked prompt, or other API errors
            blocked_reasons = [
                "SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "IMAGE_SAFETY"
            ]
            error_type = getattr(e, "code", None) or getattr(e, "reason", None) or type(e).__name__
            is_blocked = False
            is_rate_limited = False
            is_server_error = False
            # Detect rate limit error
            if hasattr(e, "code") and e.code == 429:
                is_rate_limited = True
            # Detect blocked prompt
            if hasattr(e, "code") and e.code in (400, 403):
                is_blocked = True
            if hasattr(e, "message") and any(reason in e.message.upper() for reason in blocked_reasons):
                is_blocked = True
            # Detect server error
            if hasattr(e, "code") and e.code == 500:
                is_server_error = True
            try:
                if getattr(self, "_tracing", None):
                    self._tracing.add_metadata({
                        "event": "llm.error",
                        "provider": self.name,
                        "model": req.model,
                        "error_type": error_type,
                        "message": str(e),
                    })
            except Exception:
                pass
            if is_rate_limited:
                raise RateLimitError(str(e))
            if is_blocked:
                raise ProviderError(f"Gemini blocked prompt: {e}")
            if is_server_error:
                raise TransientError(str(e))
            raise ProviderError(str(e))
    # RateLimitExceeded is now handled by APIError above
    # ServerError is now handled by APIError above
        except Exception as e:  # noqa: BLE001
            try:
                if getattr(self, "_tracing", None):
                    self._tracing.add_metadata({
                        "event": "llm.error",
                        "provider": self.name,
                        "model": req.model,
                        "error_type": type(e).__name__,
                        "message": str(e),
                    })
            except Exception:
                pass
            raise ProviderError(str(e))
