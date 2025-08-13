import asyncio
from unittest.mock import patch

from faciliter_lib.llm.adapters import LangChainChatAdapter, LlamaIndexCustomLLM
from faciliter_lib.llm.core import ChatRequest, ChatResponse, Usage


class FakeProvider:
    name = "fake"

    async def chat(self, req: ChatRequest) -> ChatResponse:
        return ChatResponse(content="hello", usage=Usage(input_tokens=1, output_tokens=1))


def test_langchain_adapter_invoke(monkeypatch):
    with patch("faciliter_lib.llm.llm_client._provider_factory", lambda name: FakeProvider()):
        adapter = LangChainChatAdapter("gemini", "m")
        out = adapter.invoke([{ "role": "user", "content": "hi" }])
        assert out["content"] == "hello"


def test_llamaindex_adapter_complete(monkeypatch):
    with patch("faciliter_lib.llm.llm_client._provider_factory", lambda name: FakeProvider()):
        custom = LlamaIndexCustomLLM("gemini", "m")
        out = custom.complete("hi")
        assert out == "hello"
