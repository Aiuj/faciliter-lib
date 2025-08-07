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
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        }
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create Gemini configuration from environment variables."""
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS")) if os.getenv("GEMINI_MAX_TOKENS") else None,
            thinking_enabled=os.getenv("GEMINI_THINKING_ENABLED", "false").lower() == "true",
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
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
