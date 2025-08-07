"""LLM module for faciliter-lib.

This module provides abstractions for working with different LLM providers
including Google Gemini and local Ollama APIs.
"""

from .llm_config import LLMConfig, GeminiConfig, OllamaConfig
from .llm_client import LLMClient
from .utils import create_gemini_client, create_ollama_client, create_client_from_env
from .json_parser import clean_and_parse_json_response

__all__ = [
    "LLMConfig", 
    "GeminiConfig", 
    "OllamaConfig", 
    "LLMClient",
    "create_gemini_client",
    "create_ollama_client", 
    "create_client_from_env",
    "clean_and_parse_json_response"
]
