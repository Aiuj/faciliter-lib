"""Configuration classes for LLM providers and selection policy."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


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

    def to_extra(self) -> Dict[str, Any]:
        """Provider-specific extras (keys, endpoints)."""
        return {}


@dataclass
class GeminiConfig(LLMConfig):
    """Configuration for Google Gemini API."""
    
    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com"
    safety_settings: Optional[Dict[str, Any]] = None
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash-lite",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        thinking_enabled: bool = False,
        base_url: str = "https://generativelanguage.googleapis.com",
        safety_settings: Optional[Dict[str, Any]] = None
    ):
        super().__init__("gemini", model, temperature, max_tokens, thinking_enabled)
        self.api_key = api_key
        self.base_url = base_url
        self.safety_settings = safety_settings or {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        }
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create Gemini configuration from environment variables.
        Supports both GEMINI_ and GOOGLE_GENAI_ prefixes (GEMINI_API_KEY or GOOGLE_GENAI_API_KEY, etc)."""
        def get_env(*keys, default=None):
            for k in keys:
                v = os.getenv(k)
                if v is not None:
                    return v
            return default

        max_tokens_val = get_env("GEMINI_MAX_TOKENS", "GOOGLE_GENAI_MAX_TOKENS")

        return cls(
            api_key=get_env("GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY", default=""),
            model=get_env("GEMINI_MODEL", "GOOGLE_GENAI_MODEL", "GOOGLE_GENAI_MODEL_DEFAULT", default="gemini-2.5-flash-lite"),
            temperature=float(get_env("GEMINI_TEMPERATURE", "GOOGLE_GENAI_TEMPERATURE", default="0.1")),
            max_tokens=int(max_tokens_val) if max_tokens_val is not None else None,
            thinking_enabled=get_env("GEMINI_THINKING_ENABLED", "GOOGLE_GENAI_THINKING_ENABLED", default="false").lower() == "true",
            base_url=get_env("GEMINI_BASE_URL", "GOOGLE_GENAI_BASE_URL", default="https://generativelanguage.googleapis.com"),
        )

    def to_extra(self) -> Dict[str, Any]:
        return {"api_key": self.api_key, "base_url": self.base_url}


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
        model: str = "llama3.2",
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
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
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

    def to_extra(self) -> Dict[str, Any]:
        return {"base_url": self.base_url}


@dataclass
class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI/Azure OpenAI."""

    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Azure: https://{resource}.openai.azure.com/openai/deployments/{deployment}

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__("openai", model, temperature, max_tokens, False)
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        return cls(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS")) if os.getenv("OPENAI_MAX_TOKENS") else None,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )

    def to_extra(self) -> Dict[str, Any]:
        return {"api_key": self.api_key, "base_url": self.base_url}


@dataclass
class MistralConfig(LLMConfig):
    api_key: Optional[str] = None

    def __init__(
        self,
        model: str = "mistral-small",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__("mistral", model, temperature, max_tokens, False)
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> "MistralConfig":
        return cls(
            model=os.getenv("MISTRAL_MODEL", "mistral-small"),
            temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MISTRAL_MAX_TOKENS")) if os.getenv("MISTRAL_MAX_TOKENS") else None,
            api_key=os.getenv("MISTRAL_API_KEY"),
        )

    def to_extra(self) -> Dict[str, Any]:
        return {"api_key": self.api_key}


@dataclass
class ProviderPolicy:
    """Preferred models per provider by cost tier."""

    low: List[str]
    medium: List[str]
    high: List[str]


@dataclass
class LLMPolicy:
    """Centralized policy/config for providers and their preferred models."""

    gemini: ProviderPolicy = field(default_factory=lambda: ProviderPolicy(low=["gemini-1.5-flash"], medium=["gemini-1.5-pro"], high=["gemini-2.0-pro-exp"]))
    openai: ProviderPolicy = field(default_factory=lambda: ProviderPolicy(low=["gpt-4o-mini"], medium=["gpt-4o"], high=["o4-mini", "o4"]))
    mistral: ProviderPolicy = field(default_factory=lambda: ProviderPolicy(low=["mistral-small"], medium=["mistral-medium"], high=["mistral-large-latest"]))
    ollama: ProviderPolicy = field(default_factory=lambda: ProviderPolicy(low=["llama3.2"], medium=["llama3.1:8b"], high=["llama3.1:70b"]))
