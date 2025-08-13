"""Utility functions for creating LLM clients."""

from typing import Optional, Dict, Any
from .llm_config import LLMConfig, GeminiConfig, OllamaConfig, OpenAIConfig, MistralConfig
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
    provider: str = "ollama",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    max_tokens: Optional[int] = None,
    thinking_enabled: Optional[bool] = None,
) -> LLMClient:
    """Create an LLM client from environment variables.
    
    Args:
        provider: Provider name ("gemini", "openai"/"azure", "mistral", or "ollama").
        model: Optional model/deployment name to override the value from env.
        temperature: Optional temperature override.
        base_url: Optional base URL override (applies to providers supporting base_url).
        max_tokens: Optional max tokens override.
        thinking_enabled: Optional flag to enable/disable chain-of-thought style behavior when supported.
        
    Returns:
        Configured LLMClient instance
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider.lower() in ("gemini", "google", "vertex"):
        config = GeminiConfig.from_env()
    elif provider.lower() in ("openai", "azure-openai", "azure"):
        config = OpenAIConfig.from_env()
    elif provider.lower() == "mistral":
        config = MistralConfig.from_env()
    elif provider.lower() == "ollama":
        config = OllamaConfig.from_env()
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Apply overrides when provided and supported by the config
    if model is not None and hasattr(config, "model"):
        config.model = model  # type: ignore[attr-defined]
    if temperature is not None and hasattr(config, "temperature"):
        config.temperature = temperature  # type: ignore[attr-defined]
    if max_tokens is not None and hasattr(config, "max_tokens"):
        config.max_tokens = max_tokens  # type: ignore[attr-defined]
    if thinking_enabled is not None and hasattr(config, "thinking_enabled"):
        config.thinking_enabled = thinking_enabled  # type: ignore[attr-defined]
    if base_url is not None and hasattr(config, "base_url"):
        config.base_url = base_url  # type: ignore[attr-defined]
    
    return LLMClient(config)
