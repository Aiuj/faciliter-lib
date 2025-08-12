"""Tests for LLM functionality."""

import pytest
from unittest.mock import patch
from pydantic import BaseModel
from typing import Optional

from faciliter_lib.llm import (
    LLMClient,
    GeminiConfig,
    OllamaConfig,
    create_ollama_client,
    create_gemini_client,
)


class WeatherResponse(BaseModel):
    """Test model for structured output."""

    location: str
    temperature: float
    condition: str
    humidity: Optional[int] = None


class TestLLMConfig:
    """Test configuration classes."""

    def test_gemini_config_creation(self):
        config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash", temperature=0.5)
        assert config.provider == "gemini"
        assert config.api_key == "test-key"
        assert config.model == "gemini-1.5-flash"
        assert config.temperature == 0.5
        assert config.safety_settings is not None

    def test_ollama_config_creation(self):
        config = OllamaConfig(model="llama3.2", temperature=0.7, base_url="http://localhost:11434")
        assert config.provider == "ollama"
        assert config.model == "llama3.2"
        assert config.temperature == 0.7
        assert config.base_url == "http://localhost:11434"

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-api-key", "GEMINI_MODEL": "gemini-pro", "GEMINI_TEMPERATURE": "0.3"})
    def test_gemini_config_from_env(self):
        config = GeminiConfig.from_env()
        assert config.api_key == "test-api-key"
        assert config.model == "gemini-pro"
        assert config.temperature == 0.3

    @patch.dict("os.environ", {"OLLAMA_MODEL": "llama3.1", "OLLAMA_TEMPERATURE": "0.8", "OLLAMA_BASE_URL": "http://custom:11434"})
    def test_ollama_config_from_env(self):
        config = OllamaConfig.from_env()
        assert config.model == "llama3.1"
        assert config.temperature == 0.8
        assert config.base_url == "http://custom:11434"


class TestLLMClient:
    @patch("faciliter_lib.llm.llm_client.OllamaProvider")
    def test_ollama_client_initialization(self, mock_ollama):
        config = OllamaConfig(model="llama3.2", temperature=0.7)
        client = LLMClient(config)
        mock_ollama.assert_called_once()
        assert client.config == config

    @patch("faciliter_lib.llm.llm_client.GoogleGenAIProvider")
    def test_gemini_client_initialization(self, mock_gemini):
        config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash", temperature=0.5)
        client = LLMClient(config)
        mock_gemini.assert_called_once()
        assert client.config == config

    def test_unsupported_provider(self):
        class UnsupportedConfig:
            provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMClient(UnsupportedConfig())

    def test_normalize_messages_string(self):
        config = OllamaConfig(model="test")
        with patch("faciliter_lib.llm.llm_client.OllamaProvider"):
            client = LLMClient(config)
            messages = client._normalize_messages("Hello world")
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "Hello world"

    def test_normalize_messages_list(self):
        config = OllamaConfig(model="test")
        with patch("faciliter_lib.llm.llm_client.OllamaProvider"):
            client = LLMClient(config)
            input_messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "system", "content": "You are helpful"},
            ]
            messages = client._normalize_messages(input_messages)
            assert len(messages) == 3
            assert messages[0]["content"] == "Hello"
            assert messages[1]["content"] == "Hi there"
            assert messages[2]["content"] == "You are helpful"

    def test_get_model_info(self):
        config = OllamaConfig(model="llama3.2", temperature=0.7, thinking_enabled=True)
        with patch("faciliter_lib.llm.llm_client.OllamaProvider"):
            client = LLMClient(config)
            info = client.get_model_info()
            assert info["provider"] == "ollama"
            assert info["model"] == "llama3.2"
            assert info["temperature"] == 0.7
            assert info["thinking_enabled"] is True


class TestUtilityFunctions:
    @patch("faciliter_lib.llm.utils.LLMClient")
    def test_create_ollama_client(self, mock_client_class):
        client = create_ollama_client(model="llama3.2", temperature=0.8, thinking_enabled=True)
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[0][0]
        assert call_args.model == "llama3.2"
        assert call_args.temperature == 0.8
        assert call_args.thinking_enabled is True
        assert call_args.provider == "ollama"

    @patch("faciliter_lib.llm.utils.LLMClient")
    def test_create_gemini_client_with_key(self, mock_client_class):
        client = create_gemini_client(api_key="test-key", model="gemini-pro", temperature=0.3)
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[0][0]
        assert call_args.api_key == "test-key"
        assert call_args.model == "gemini-pro"
        assert call_args.temperature == 0.3
        assert call_args.provider == "gemini"


class TestIntegration:
    @pytest.mark.skip(reason="Requires running Ollama service")
    def test_ollama_integration(self):
        client = create_ollama_client(model="llama3.2")
        response = client.chat("Say hello in one word")
        assert "content" in response
        assert response["content"] is not None
        assert response["structured"] is False

    @pytest.mark.skip(reason="Requires valid Gemini API key")
    def test_gemini_integration(self):
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        client = create_gemini_client(api_key=api_key)
        response = client.chat("Say hello in one word")
        assert "content" in response
        assert response["content"] is not None
        assert response["structured"] is False


if __name__ == "__main__":
    pytest.main([__file__])
