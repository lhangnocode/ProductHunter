from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.agent.prompts import system_prompt_for_request
from app.agent.schemas import AgentChatRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

ToolEventCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


def _require_openai_config() -> None:
    api_key = settings.AGENT_OPENAI_API_KEY or settings.DASHSCOPE_API_KEY
    if not api_key:
        raise RuntimeError("No API key configured: set AGENT_OPENAI_API_KEY or DASHSCOPE_API_KEY")


def _build_llm() -> ChatOpenAI:
    api_key = settings.AGENT_OPENAI_API_KEY or settings.DASHSCOPE_API_KEY
    base_url = settings.AGENT_OPENAI_BASE_URL or settings.QWEN_BASE_URL
    model = settings.AGENT_OPENAI_MODEL or settings.QWEN_MODEL
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": settings.AGENT_OPENAI_TEMPERATURE,
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def _tool_descriptions(tools: list[BaseTool]) -> str:
    lines = ["CÁC CÔNG CỤ (TOOL) CÓ SẴN:"]
    for t in tools:
        lines.append(f"- {t.name}: {t.description}")
    return "\n".join(lines)


def _build_agent(
    request: AgentChatRequest,
    llm: ChatOpenAI,
    tools: list[BaseTool],
) -> Any:
    full_system_prompt = f"{system_prompt_for_request(request)}\n\n{_tool_descriptions(tools)}"
    return create_agent(llm, tools, system_prompt=full_system_prompt)


def _extract_answer(result: dict[str, Any]) -> str | None:
    messages = result.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
    output = result.get("output")
    if isinstance(output, str):
        return output
    return None


async def run_langchain_agent(
    request: AgentChatRequest,
    tools: list[BaseTool],
    on_tool_event: ToolEventCallback | None = None,
    on_token: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    _require_openai_config()
    llm = _build_llm()
    agent = _build_agent(request, llm, tools)

    max_loops = settings.AGENT_MAX_ITERATIONS
    recursion_limit = max_loops * 2 + 5
    config: RunnableConfig = {"recursion_limit": recursion_limit}

    input_messages = [HumanMessage(content=request.message)]
    result = await agent.ainvoke(
        {"messages": input_messages},
        config=config,
    )

    answer = _extract_answer(result)
    if not answer:
        raise ValueError(f"Agent output invalid: {json.dumps(result, default=str, ensure_ascii=False)}")

    if on_token:
        await on_token(answer)

    return answer


async def run_langchain_agent_stream(
    request: AgentChatRequest,
    tools: list[BaseTool],
    on_tool_event: ToolEventCallback | None = None,
    on_token: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    _require_openai_config()
    llm = _build_llm()
    agent = _build_agent(request, llm, tools)

    max_loops = settings.AGENT_MAX_ITERATIONS
    recursion_limit = max_loops * 2 + 5
    config: RunnableConfig = {"recursion_limit": recursion_limit}

    input_messages = [HumanMessage(content=request.message)]
    inputs = {"messages": input_messages}

    answer_parts: list[str] = []
    last_tool: dict[str, Any] | None = None

    async for event in agent.astream_events(inputs, config=config, version="v2"):
        kind = event["event"]
        name = event.get("name", "")

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                answer_parts.append(chunk.content)
                if on_token:
                    await on_token(chunk.content)

        elif kind == "on_tool_start" and on_tool_event:
            tool_input = event["data"].get("input", "")
            last_tool = {
                "tool_name": name,
                "input": tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)},
            }
            await on_tool_event(
                "tool.started",
                {"tool_name": name, "input": last_tool["input"]},
            )

        elif kind == "on_tool_end" and on_tool_event:
            tool_output = event["data"].get("output", "")
            output_str = str(tool_output)
            await on_tool_event(
                "tool.finished",
                {
                    "tool_name": name,
                    "output": output_str[:1000],
                    "status": "success",
                },
            )

    answer = "".join(answer_parts).strip()
    if not answer:
        raise ValueError("Agent produced no output tokens")

    return answer
