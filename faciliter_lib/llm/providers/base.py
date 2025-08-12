"""Base provider contract for native SDK adapters.

Providers must implement the `chat` method that accepts OpenAI-style messages
and optional tools/structured output and returns a unified dict.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from ..llm_config import LLMConfig


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    def chat(
        self,
        *,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat to the provider and return a unified response dict.

        Expected return shape:
        - content: str | dict | BaseModel | None
        - structured: bool
        - tool_calls: list[dict]
        - usage: dict
        - error: optional string on failure
        """
        raise NotImplementedError
