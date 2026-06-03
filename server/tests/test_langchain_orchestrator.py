from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from app.agent.langchain_orchestrator import (
    _EventCallbackHandler,
    _extract_answer,
    _require_openai_config,
    run_langchain_agent,
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


class TestEventCallbackHandler:
    @pytest.mark.asyncio
    async def test_on_tool_start_emits_event(self) -> None:
        callback = AsyncMock()
        handler = _EventCallbackHandler(on_tool_event=callback)
        await handler.on_tool_start(
            {"name": "search_products"},
            "query",
            inputs={"query": "iphone"},
        )
        callback.assert_awaited_once_with(
            "tool.started",
            {"tool_name": "search_products", "input": {"query": "iphone"}},
        )

    @pytest.mark.asyncio
    async def test_on_tool_start_uses_kwargs_fallback(self) -> None:
        callback = AsyncMock()
        handler = _EventCallbackHandler(on_tool_event=callback)
        await handler.on_tool_start(
            {"kwargs": {"name": "from_kwargs"}},
            "input",
        )
        callback.assert_awaited_once_with(
            "tool.started",
            {"tool_name": "from_kwargs", "input": {}},
        )

    @pytest.mark.asyncio
    async def test_on_tool_end_emits_event(self) -> None:
        callback = AsyncMock()
        handler = _EventCallbackHandler(on_tool_event=callback)
        await handler.on_tool_end("output data")
        callback.assert_awaited_once_with(
            "tool.finished",
            {"tool_name": "tool", "output": "output data", "status": "success"},
        )

    @pytest.mark.asyncio
    async def test_on_llm_new_token_emits_token(self) -> None:
        callback = AsyncMock()
        handler = _EventCallbackHandler(on_token=callback)
        await handler.on_llm_new_token("hello")
        callback.assert_awaited_once_with("hello")

    @pytest.mark.asyncio
    async def test_noop_when_no_callbacks(self) -> None:
        handler = _EventCallbackHandler()
        await handler.on_tool_start({"name": "x"}, "input")
        await handler.on_tool_end("output")
        await handler.on_llm_new_token("token")


_MOCK_SETTINGS = {
    "AGENT_OPENAI_API_KEY": "sk-test",
    "AGENT_OPENAI_BASE_URL": "",
    "AGENT_OPENAI_MODEL": "gpt-4o-mini",
    "AGENT_OPENAI_TEMPERATURE": 0.2,
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
    async def test_passes_tool_event_callback(self) -> None:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [AIMessage(content="done")]
        }
        on_tool_event = AsyncMock()

        with (
            patch("app.agent.langchain_orchestrator.settings") as mock_settings,
            patch("app.agent.langchain_orchestrator.create_agent", return_value=mock_agent),
        ):
            for k, v in _MOCK_SETTINGS.items():
                setattr(mock_settings, k, v)

            await run_langchain_agent(
                _make_request(),
                [dummy_tool],
                on_tool_event=on_tool_event,
            )

            config = mock_agent.ainvoke.call_args[1].get("config") or {}
            callbacks = config.get("callbacks", [])
            assert len(callbacks) == 1
            assert isinstance(callbacks[0], _EventCallbackHandler)
