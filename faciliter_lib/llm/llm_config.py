"""Configuration classes for LLM providers."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


class LLMConfig(ABC):
    """Base configuration class for LLM providers."""
    
    def __init__(
        self,
        provider: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_enabled: bool = False
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.thinking_enabled = thinking_enabled
    
    @classmethod
    @abstractmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        pass


@dataclass
class GeminiConfig(LLMConfig):
    """Configuration for Google Gemini API."""
    
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
        safety_settings: Optional[Dict[str, Any]] = None
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
        """Create Gemini configuration from environment variables."""
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


@dataclass
class OpenAIConfig(LLMConfig):
        """Configuration for OpenAI-compatible APIs (OpenAI, Azure OpenAI, proxies).

        Supports three common modes:
        - OpenAI: Provide ``api_key`` (and optional ``organization``/``project``).
        - Azure OpenAI: Provide ``azure_endpoint`` and ``azure_api_version`` with
            ``api_key``; the Azure-specific client will be used.
        - OpenAI-compatible (e.g., Ollama/LiteLLM/vLLM): Provide ``base_url`` and
            ``api_key`` (often any non-empty string for local gateways).
        """

        api_key: str
        base_url: Optional[str] = None
        organization: Optional[str] = None
        project: Optional[str] = None
        # Azure-specific
        azure_endpoint: Optional[str] = None
        azure_api_version: Optional[str] = None

        def __init__(
                self,
                api_key: str,
                model: str = "gpt-4o-mini",
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                thinking_enabled: bool = False,
                base_url: Optional[str] = None,
                organization: Optional[str] = None,
                project: Optional[str] = None,
                azure_endpoint: Optional[str] = None,
                azure_api_version: Optional[str] = None,
        ):
                super().__init__("openai", model, temperature, max_tokens, thinking_enabled)
                self.api_key = api_key
                self.base_url = base_url
                self.organization = organization
                self.project = project
                self.azure_endpoint = azure_endpoint
                self.azure_api_version = azure_api_version

        @classmethod
        def from_env(cls) -> "OpenAIConfig":
                """Create OpenAI configuration from environment variables.

                Environment variables supported:
                - OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS,
                    OPENAI_BASE_URL, OPENAI_ORG, OPENAI_ORGANIZATION, OPENAI_PROJECT
                - Azure: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION,
                    AZURE_OPENAI_DEPLOYMENT (maps to ``model`` if provided)
                """

                def getenv(*names: str, default: Optional[str] = None) -> Optional[str]:
                        for n in names:
                                v = os.getenv(n)
                                if v is not None:
                                        return v
                        return default

                # Prefer Azure when endpoint is present
                azure_endpoint = getenv("AZURE_OPENAI_ENDPOINT")
                api_key = getenv("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY", default="") or ""
                model = getenv("AZURE_OPENAI_DEPLOYMENT", "OPENAI_MODEL", default="gpt-4o-mini") or "gpt-4o-mini"
                temperature = float(getenv("OPENAI_TEMPERATURE", default="0.7") or 0.7)
                max_tokens_env = getenv("OPENAI_MAX_TOKENS")
                max_tokens = int(max_tokens_env) if max_tokens_env else None
                base_url = getenv("OPENAI_BASE_URL")
                organization = getenv("OPENAI_ORG", "OPENAI_ORGANIZATION")
                project = getenv("OPENAI_PROJECT")
                azure_api_version = getenv("AZURE_OPENAI_API_VERSION", default="2024-08-01-preview")

                return cls(
                        api_key=api_key,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        base_url=base_url,
                        organization=organization,
                        project=project,
                        azure_endpoint=azure_endpoint,
                        azure_api_version=azure_api_version,
                )

@dataclass
class OllamaConfig(LLMConfig):
    """Configuration for local Ollama API."""
    
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    num_ctx: Optional[int] = None  # Context window size
    num_predict: Optional[int] = None  # Max tokens to predict
    repeat_penalty: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    
    def __init__(
        self,
        model: str = "qwen3:1.7b",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_enabled: bool = False,
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
        num_ctx: Optional[int] = None,
        num_predict: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None
    ):
        super().__init__("ollama", model, temperature, max_tokens, thinking_enabled)
        self.base_url = base_url
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.repeat_penalty = repeat_penalty
        self.top_k = top_k
        self.top_p = top_p
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Create Ollama configuration from environment variables."""
        return cls(
            model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS")) if os.getenv("OLLAMA_MAX_TOKENS") else None,
            thinking_enabled=os.getenv("OLLAMA_THINKING_ENABLED", "false").lower() == "true",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX")) if os.getenv("OLLAMA_NUM_CTX") else None,
            num_predict=int(os.getenv("OLLAMA_NUM_PREDICT")) if os.getenv("OLLAMA_NUM_PREDICT") else None,
            repeat_penalty=float(os.getenv("OLLAMA_REPEAT_PENALTY")) if os.getenv("OLLAMA_REPEAT_PENALTY") else None,
            top_k=int(os.getenv("OLLAMA_TOP_K")) if os.getenv("OLLAMA_TOP_K") else None,
            top_p=float(os.getenv("OLLAMA_TOP_P")) if os.getenv("OLLAMA_TOP_P") else None,
        )
