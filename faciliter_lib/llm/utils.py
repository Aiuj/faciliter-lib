"""Utility functions for creating LLM clients."""

from typing import Optional, Dict, Any
import os
from .llm_config import LLMConfig, GeminiConfig, OllamaConfig
from .llm_client import LLMClient


def create_gemini_client(
    api_key: Optional[str] = None,
    model: str = "gemini-1.5-flash",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    thinking_enabled: bool = False,
    **kwargs
) -> LLMClient:
    """Create a Gemini LLM client.
    
    Args:
        api_key: Google API key (if None, will try to get from environment)
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        thinking_enabled: Whether to enable step-by-step thinking
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLMClient instance
    """
    if api_key is None:
        config = GeminiConfig.from_env()
        # Override with provided parameters
        config.model = model
        config.temperature = temperature
        config.max_tokens = max_tokens
        config.thinking_enabled = thinking_enabled
    else:
        config = GeminiConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_enabled=thinking_enabled,
            **kwargs
        )
    
    return LLMClient(config)


def create_ollama_client(
    model: str = "llama3.2",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    thinking_enabled: bool = False,
    **kwargs
) -> LLMClient:
    """Create an Ollama LLM client.
    
    Args:
        model: Model name to use
        base_url: Ollama server URL
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        thinking_enabled: Whether to enable step-by-step thinking
        **kwargs: Additional configuration parameters (num_ctx, top_p, etc.)
        
    Returns:
        Configured LLMClient instance
    """
    config = OllamaConfig(
        model=model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_enabled=thinking_enabled,
        **kwargs
    )
    
    return LLMClient(config)


def create_client_from_env(
    provider: Optional[str] = None,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    thinking_enabled: Optional[bool] = None,
    **kwargs: Any,
) -> LLMClient:
    """Create an LLM client from environment variables with optional overrides.

    Args:
        provider: Provider name ("gemini" or "ollama"). If None, uses LLM_PROVIDER or defaults to "ollama".
        model: Optional model name override.
        base_url: Optional base URL override.
        temperature: Optional temperature override.
        max_tokens: Optional max tokens override.
        thinking_enabled: Optional thinking flag override.
        **kwargs: Additional configuration overrides applied when supported by the provider
            (e.g., Ollama: timeout, num_ctx, num_predict, repeat_penalty, top_k, top_p;
                   Gemini: safety_settings).

    Returns:
        Configured LLMClient instance.

    Raises:
        ValueError: If provider is not supported.
    """
    # Determine provider
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", "ollama")
    provider_lc = provider.lower()

    # Build base config from env
    if provider_lc in ("gemini", "google"):
        config = GeminiConfig.from_env()
    elif provider_lc == "ollama":
        config = OllamaConfig.from_env()
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Apply common overrides when provided
    if model is not None:
        config.model = model
    if temperature is not None:
        config.temperature = temperature
    if max_tokens is not None:
        config.max_tokens = max_tokens
    if thinking_enabled is not None:
        config.thinking_enabled = thinking_enabled
    if base_url is not None and hasattr(config, "base_url"):
        config.base_url = base_url

    # Apply provider-specific overrides from kwargs if attribute exists
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return LLMClient(config)
