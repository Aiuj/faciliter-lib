"""Google GenAI provider using the official google.genai SDK.

Docs consulted via Context7 show structured outputs with Pydantic are supported
by passing response_mime_type='application/json' and response_schema=MyModel to
GenerateContentConfig, and chat via client.chats.create(...).send_message(...).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .base import BaseProvider
from ..llm_config import LLMConfig
from dataclasses import dataclass
from typing import Optional, Dict, Any
from faciliter_lib import get_module_logger
from faciliter_lib.tracing.tracing import add_trace_metadata
from faciliter_lib.tracing.service_usage import log_llm_usage
from faciliter_lib.llm.rate_limiter import RateLimitConfig, RateLimiter
from faciliter_lib.llm.retry import RetryConfig, retry_handler

logger = get_module_logger()


@dataclass
class GeminiConfig(LLMConfig):
    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com"
    safety_settings: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_enabled: bool = False,
        base_url: str = "https://generativelanguage.googleapis.com",
        safety_settings: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("gemini", model, temperature, max_tokens, thinking_enabled)
        self.api_key = api_key
        self.base_url = base_url
        self.safety_settings = safety_settings or {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
        }

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        import os

        def get_env(*names, default=None):
            for name in names:
                val = os.getenv(name)
                if val is not None:
                    return val
            return default

        api_key = get_env("GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY", default="")
        model = get_env("GEMINI_MODEL", "GOOGLE_GENAI_MODEL", "GOOGLE_GENAI_MODEL_DEFAULT", default="gemini-1.5-flash")
        temperature = float(get_env("GEMINI_TEMPERATURE", "GOOGLE_GENAI_TEMPERATURE", default="0.1"))
        max_tokens_env = get_env("GEMINI_MAX_TOKENS", "GOOGLE_GENAI_MAX_TOKENS")
        max_tokens = int(max_tokens_env) if max_tokens_env is not None else None
        thinking_enabled = get_env("GEMINI_THINKING_ENABLED", "GOOGLE_GENAI_THINKING_ENABLED", default="false").lower() == "true"
        base_url = get_env("GEMINI_BASE_URL", "GOOGLE_GENAI_BASE_URL", default="https://generativelanguage.googleapis.com")

        return cls(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_enabled=thinking_enabled,
            base_url=base_url,
        )

class GoogleGenAIProvider(BaseProvider):
    """Provider implementation for Google GenAI (Gemini).

    Includes a lightweight in-process rate limiter enforcing per-model
    requests-per-minute (RPM) ceilings derived from a hardcoded table. Token
    and daily limits are currently not enforced client-side. The limiter is
    best-effort and fail-soft: if acquisition raises, the request proceeds.
    
    Also includes retry logic with exponential backoff for transient failures
    such as rate limits, server errors, and network issues.
    """

    # Hardcoded per-model request-per-minute limits. Keys are lowercase substrings
    # we expect to find in the configured model name for a match. These values
    # reflect only RPM (requests per minute); TPM/RPD intentionally ignored for now.
    _MODEL_RPM: Dict[str, int] = {
        "gemini-2.5-pro": 5,          # Gemini 2.5 Pro
        "gemini-2.5-flash-lite": 15,  # Gemini 2.5 Flash-Lite
        "gemini-2.5-flash": 10,       # Gemini 2.5 Flash (keep after flash-lite for matching specificity)
        "gemma-3": 30,         # Gemma 3
        "embedding": 100,      # Gemini Embedding models
    }

    def __init__(self, config: GeminiConfig) -> None:  # type: ignore[override]
        super().__init__(config)

        # Lazy import to avoid hard dependency if unused
        from google import genai  # type: ignore

        # Build client; supports API key from env or passed explicitly
        # Gemini Developer API (default). Vertex AI could be added later.
        self._client = genai.Client(api_key=config.api_key)

        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        GoogleGenAIInstrumentor().instrument()

        # Initialize a rate limiter based on model RPM. We derive a conservative
        # per-second rate as max(1, RPM/60). If model not found, default to 60 RPM.
        model_lc = (config.model or "").lower()
        rpm = 60  # default fallback
        # Choose the most specific matching key (longest substring match)
        matches = [k for k in self._MODEL_RPM.keys() if k in model_lc]
        if matches:
            matches.sort(key=len, reverse=True)
            rpm = self._MODEL_RPM[matches[0]]
        rps = max(1.0 / 60.0, rpm / 60.0)  # ensure non-zero; may be fractional
        self._rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=rpm, requests_per_second=rps)
        )
        logger.debug(
            "Initialized Gemini rate limiter",
            extra={"model": config.model, "rpm": rpm, "rps": rps},
        )

        # Configure retry logic for common transient failures
        # Identify retryable exceptions from google-genai and google.api_core
        retryable_exceptions = []
        try:
            from google.api_core import exceptions as gac_exceptions
            retryable_exceptions.extend([
                gac_exceptions.ResourceExhausted,     # 429 rate limits
                gac_exceptions.ServiceUnavailable,    # 503 service unavailable
                gac_exceptions.InternalServerError,   # 500 internal errors
                gac_exceptions.DeadlineExceeded,      # 504 gateway timeout
                gac_exceptions.TooManyRequests,       # Additional rate limit variant
            ])
        except ImportError:
            # google.api_core might not be available in all setups
            pass

        # Add google.genai specific errors (503 ServerError, etc.)
        try:
            from google.genai import errors as genai_errors
            retryable_exceptions.extend([
                genai_errors.ServerError,             # 503 server overloaded, 500 internal errors
                genai_errors.ClientError,             # 429 rate limits and other 4xx retryable errors
            ])
        except ImportError:
            # google.genai might not be available
            pass

        # Add common network-level exceptions
        retryable_exceptions.extend([
            ConnectionError,
            TimeoutError,
        ])

        self._retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retry_on_exceptions=tuple(retryable_exceptions) if retryable_exceptions else (Exception,),
        )
        logger.debug(
            "Initialized Gemini retry config",
            extra={"max_retries": self._retry_config.max_retries, "retryable_exceptions_count": len(retryable_exceptions)},
        )

    def close(self) -> None:  # type: ignore[override]
        """Close the underlying google-genai client."""
        client = getattr(self, "_client", None)
        if client is None:
            return
        try:
            close_method = getattr(client, "close", None)
            if callable(close_method):
                close_method()
        except Exception as exc:
            logger.debug("Gemini client close failed", extra={"error": str(exc)})

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

    def _acquire_rate_limit(self) -> None:
        """Acquire the rate limiter slot.

        The provider's public interface is synchronous, but the RateLimiter is
        asyncio-based. This method handles the async rate limiter with proper
        timeout and thread-safety for both sync and async contexts.
        """
        try:
            import asyncio
            import concurrent.futures
            
            # Short timeout since rate limiting should be fast
            MAX_TIMEOUT = 5.0
            
            async def _acquire_with_timeout():
                """Acquire with timeout wrapper."""
                try:
                    await asyncio.wait_for(
                        self._rate_limiter.acquire(), 
                        timeout=MAX_TIMEOUT
                    )
                    return True
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Rate limiter acquisition timed out after {MAX_TIMEOUT}s"
                    )
                    return False
            
            def _run_in_new_loop():
                """Run the async function in a new event loop."""
                return asyncio.run(_acquire_with_timeout())
            
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - use thread executor
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_run_in_new_loop)
                    future.result(timeout=MAX_TIMEOUT + 1.0)
            except RuntimeError:
                # No running loop - standard case for sync calls
                asyncio.run(_acquire_with_timeout())
                    
        except Exception as e:
            # Never block the call due to rate limiter errors
            logger.warning(
                "Rate limiter acquisition failed; proceeding without throttle",
                exc_info=e
            )

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
        """Main chat interface with rate limiting and retry logic."""
        try:
            # Enforce model-specific RPM throttling before performing network call.
            self._acquire_rate_limit()
            
            # Call the actual API with retry logic
            return self._chat_with_retry(
                messages=messages,
                tools=tools,
                structured_output=structured_output,
                system_message=system_message,
                use_search_grounding=use_search_grounding,
                thinking_enabled=thinking_enabled,
            )
        except Exception as e:  # pragma: no cover - network errors
            # Log error without full traceback for retryable errors (retries already logged)
            # For non-retryable errors, include traceback for debugging
            is_retryable = isinstance(e, self._retry_config.retry_on_exceptions)
            if is_retryable:
                logger.error(f"genai.chat failed after all retries: {type(e).__name__}: {e}")
            else:
                logger.exception("genai.chat failed with non-retryable error")
            
            return {
                "error": str(e),
                "content": None,
                "structured": structured_output is not None,
                "tool_calls": [],
                "usage": {},
            }

    def _chat_with_retry(
        self,
        *,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None,
        use_search_grounding: bool = False,
        thinking_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Core API call logic with retry decoration applied."""
        
        @retry_handler(self._retry_config)
        def _make_api_call() -> Dict[str, Any]:
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

            # Log service usage to OpenTelemetry/OpenSearch (replaces Langfuse tracing)
            try:
                usage_metadata = getattr(resp, "usage_metadata", {}) or {}
                input_tokens = getattr(usage_metadata, "prompt_token_count", None) or usage_metadata.get("prompt_token_count")
                output_tokens = getattr(usage_metadata, "candidates_token_count", None) or usage_metadata.get("candidates_token_count")
                total_tokens = getattr(usage_metadata, "total_token_count", None) or usage_metadata.get("total_token_count")
                
                log_llm_usage(
                    provider="google-gemini",
                    model=self.config.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    structured=bool(structured_output),
                    has_tools=bool(tools),
                    search_grounding=use_search_grounding,
                    metadata={"single_turn": is_single_turn},
                )
            except Exception as e:
                # Service usage logging should never break the call
                logger.debug(f"Failed to log LLM usage: {e}")

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

        return _make_api_call()
