"""Embeddings Provider Configuration Settings.

This module contains configuration classes for embeddings providers
including OpenAI, Google, Hugging Face, Ollama, and local models.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .base_settings import BaseSettings, EnvParser


@dataclass(frozen=True) 
class EmbeddingsSettings(BaseSettings):
    """Embeddings provider configuration settings."""
    
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    embedding_dimension: Optional[int] = None
    task_type: Optional[str] = None
    title: Optional[str] = None
    
    # Provider-specific settings
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    google_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # Ollama settings
    ollama_host: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_timeout: Optional[int] = None
    
    # Local model settings
    device: str = "auto"
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False
    use_sentence_transformers: bool = True
    
    # Cache settings
    cache_duration_seconds: int = 7200
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "EmbeddingsSettings":
        """Create embeddings settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        provider = EnvParser.get_env("EMBEDDING_PROVIDER", default="openai")
        model = EnvParser.get_env("EMBEDDING_MODEL", default="text-embedding-3-small")
        
        settings_dict = {
            "provider": provider,
            "model": model,
            "embedding_dimension": EnvParser.get_env("EMBEDDING_DIMENSION", env_type=int),
            "task_type": EnvParser.get_env("EMBEDDING_TASK_TYPE"),
            "title": EnvParser.get_env("EMBEDDING_TITLE"),
            "api_key": EnvParser.get_env("OPENAI_API_KEY", "API_KEY"),
            "base_url": EnvParser.get_env("OPENAI_BASE_URL", "BASE_URL"),
            "organization": EnvParser.get_env("OPENAI_ORGANIZATION"),
            "project": EnvParser.get_env("OPENAI_PROJECT"),
            "google_api_key": EnvParser.get_env("GOOGLE_GENAI_API_KEY", "GEMINI_API_KEY"),
            "huggingface_api_key": EnvParser.get_env("HUGGINGFACE_API_KEY"),
            "ollama_host": EnvParser.get_env("OLLAMA_HOST"),
            "ollama_url": EnvParser.get_env("OLLAMA_URL"),
            "ollama_timeout": EnvParser.get_env("OLLAMA_TIMEOUT", env_type=int),
            "device": EnvParser.get_env("EMBEDDING_DEVICE", default="auto"),
            "cache_dir": EnvParser.get_env("EMBEDDING_CACHE_DIR"),
            "trust_remote_code": EnvParser.get_env("EMBEDDING_TRUST_REMOTE_CODE", default=False, env_type=bool),
            "use_sentence_transformers": EnvParser.get_env("EMBEDDING_USE_SENTENCE_TRANSFORMERS", default=True, env_type=bool),
            "cache_duration_seconds": EnvParser.get_env("EMBEDDING_CACHE_DURATION_SECONDS", default=7200, env_type=int),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "provider": self.provider,
            "model": self.model,
            "embedding_dimension": self.embedding_dimension,
            "task_type": self.task_type,
            "title": self.title,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "organization": self.organization,
            "project": self.project,
            "google_api_key": self.google_api_key,
            "huggingface_api_key": self.huggingface_api_key,
            "ollama_host": self.ollama_host,
            "ollama_url": self.ollama_url,
            "ollama_timeout": self.ollama_timeout,
            "device": self.device,
            "cache_dir": self.cache_dir,
            "trust_remote_code": self.trust_remote_code,
            "use_sentence_transformers": self.use_sentence_transformers,
            "cache_duration_seconds": self.cache_duration_seconds,
        }