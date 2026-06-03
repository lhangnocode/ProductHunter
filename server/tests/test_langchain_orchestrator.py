from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from app.agent.langchain_orchestrator import (
    _extract_answer,
    _require_openai_config,
    run_langchain_agent,
    run_langchain_agent_stream,
)
from app.agent.schemas import AgentChatRequest


def _make_request(message: str = "test") -> AgentChatRequest:
    return AgentChatRequest(message=message)


@tool
def dummy_tool(x: str) -> str:
    """A dummy test tool."""
    return f"result: {x}"


class TestRequireOpenAIConfig:
    def test_raises_when_no_api_key(self) -> None:
        with patch("app.agent.langchain_orchestrator.settings") as mock_settings:
            mock_settings.AGENT_OPENAI_API_KEY = ""
            mock_settings.DASHSCOPE_API_KEY = ""
            with pytest.raises(RuntimeError, match="No API key configured"):
                _require_openai_config()

    def test_passes_when_agent_api_key_set(self) -> None:
        with patch("app.agent.langchain_orchestrator.settings") as mock_settings:
            mock_settings.AGENT_OPENAI_API_KEY = "sk-test"
            mock_settings.DASHSCOPE_API_KEY = ""
            _require_openai_config()

    def test_passes_when_dashscope_key_set(self) -> None:
        with patch("app.agent.langchain_orchestrator.settings") as mock_settings:
            mock_settings.AGENT_OPENAI_API_KEY = ""
            mock_settings.DASHSCOPE_API_KEY = "sk-dashscope"
            _require_openai_config()


class TestExtractAnswer:
    def test_extracts_last_ai_message(self) -> None:
        result = {
            "messages": [
                HumanMessage(content="hello"),
                AIMessage(content="I can help"),
            ]
        }
        assert _extract_answer(result) == "I can help"

    def test_returns_none_for_empty_messages(self) -> None:
        assert _extract_answer({"messages": []}) is None

    def test_returns_none_when_no_ai_message(self) -> None:
        result = {"messages": [HumanMessage(content="hello")]}
        assert _extract_answer(result) is None

    def test_falls_back_to_output_key(self) -> None:
        result = {"output": "fallback answer", "messages": []}
        assert _extract_answer(result) == "fallback answer"

    def test_returns_none_for_invalid_output(self) -> None:
        result = {"output": 123, "messages": []}
        assert _extract_answer(result) is None


_MOCK_SETTINGS = {
    "AGENT_OPENAI_API_KEY": "sk-test",
    "AGENT_OPENAI_BASE_URL": "",
    "AGENT_OPENAI_MODEL": "gpt-4o-mini",
    "AGENT_OPENAI_TEMPERATURE": 0.2,
    "AGENT_MAX_ITERATIONS": 10,
    "DASHSCOPE_API_KEY": "",
    "QWEN_BASE_URL": "",
    "QWEN_MODEL": "qwen3.6-flash",
}


class TestRunLangchainAgent:
    @pytest.mark.asyncio
    async def test_raises_when_no_api_key(self) -> None:
        with patch("app.agent.langchain_orchestrator.settings") as mock_settings:
            mock_settings.AGENT_OPENAI_API_KEY = ""
            mock_settings.DASHSCOPE_API_KEY = ""
            with pytest.raises(RuntimeError, match="No API key configured"):
                await run_langchain_agent(
                    _make_request(),
                    [dummy_tool],
                )

    @pytest.mark.asyncio
    async def test_calls_create_agent_and_extracts_answer(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [
                HumanMessage(content="test"),
                AIMessage(content="Chào bạn, đây là gợi ý."),
            ]
        }

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent) as mock_create,
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            result = await run_langchain_agent(
                _make_request("Tư vấn giúp tôi"),
                [dummy_tool],
            )

            assert result == "Chào bạn, đây là gợi ý."
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_agent_returns_no_answer(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": []}

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            with pytest.raises(ValueError, match="Agent output invalid"):
                await run_langchain_agent(
                    _make_request(),
                    [dummy_tool],
                )

    @pytest.mark.asyncio
    async def test_calls_on_token_with_full_answer(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [AIMessage(content="full answer here")]
        }
        on_token = AsyncMock()

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            await run_langchain_agent(
                _make_request(),
                [dummy_tool],
                on_token=on_token,
            )

            on_token.assert_awaited_once_with("full answer here")


class TestRunLangchainAgentStream:
    @pytest.mark.asyncio
    async def test_raises_when_no_api_key(self) -> None:
        with patch("app.agent.langchain_orchestrator.settings") as mock_settings:
            mock_settings.AGENT_OPENAI_API_KEY = ""
            mock_settings.DASHSCOPE_API_KEY = ""
            with pytest.raises(RuntimeError, match="No API key configured"):
                await run_langchain_agent_stream(
                    _make_request(),
                    [dummy_tool],
                )

    @pytest.mark.asyncio
    async def test_collects_tokens_from_stream_events(self) -> None:
        mock_agent = AsyncMock()

        class FakeChunk:
            content = ""

        async def _mock_astream_events(*args, **kwargs):
            tokens = ["Xin ", "chào ", "bạn"]
            for token in tokens:
                chunk = FakeChunk()
                chunk.content = token
                yield {
                    "event": "on_chat_model_stream",
                    "name": "ChatOpenAI",
                    "data": {"chunk": chunk},
                }

        mock_agent.astream_events = _mock_astream_events

        on_token = AsyncMock()

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            result = await run_langchain_agent_stream(
                _make_request("hello"),
                [dummy_tool],
                on_token=on_token,
            )

            assert result == "Xin chào bạn"
            assert on_token.await_count == 3
            on_token.assert_any_await("Xin ")
            on_token.assert_any_await("chào ")
            on_token.assert_any_await("bạn")

    @pytest.mark.asyncio
    async def test_collects_tool_events(self) -> None:
        mock_agent = AsyncMock()

        class FakeChunk:
            content = ""

        async def _mock_astream_events(*args, **kwargs):
            chunk = FakeChunk()
            chunk.content = "done"
            yield {"event": "on_chat_model_stream", "name": "ChatOpenAI", "data": {"chunk": chunk}}
            yield {
                "event": "on_tool_start",
                "name": "search_products",
                "data": {"input": {"query": "iphone"}},
            }
            yield {
                "event": "on_tool_end",
                "name": "search_products",
                "data": {"output": '[{"name": "iPhone"}]'},
            }

        mock_agent.astream_events = _mock_astream_events
        on_tool = AsyncMock()

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            await run_langchain_agent_stream(
                _make_request("tìm iPhone"),
                [dummy_tool],
                on_tool_event=on_tool,
            )

            on_tool.assert_any_await(
                "tool.started",
                {"tool_name": "search_products", "input": {"query": "iphone"}},
            )
            on_tool.assert_any_await(
                "tool.finished",
                {"tool_name": "search_products", "output": '[{"name": "iPhone"}]', "status": "success"},
            )

    @pytest.mark.asyncio
    async def test_raises_when_no_tokens_produced(self) -> None:
        mock_agent = AsyncMock()

        async def _empty_stream(*args, **kwargs):
            if False:
                yield  # pragma: no cover
            return

        mock_agent.astream_events = _empty_stream

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            with pytest.raises(ValueError, match="Agent produced no output tokens"):
                await run_langchain_agent_stream(
                    _make_request(),
                    [dummy_tool],
                )
