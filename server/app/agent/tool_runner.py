from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool

from app.agent.events import AgentEventCallback, emit_event, json_safe
from app.agent.schemas import AgentToolTrace


def tool_by_name(tools: list[BaseTool], name: str) -> BaseTool:
    for tool in tools:
        if tool.name == name:
            return tool
    raise KeyError(name)


async def run_tool(
    tools: list[BaseTool],
    trace: list[AgentToolTrace],
    callback: AgentEventCallback | None,
    tool_name: str,
    tool_input: dict[str, Any],
) -> Any:
    await emit_event(callback, "tool.started", {"tool_name": tool_name, "input": tool_input})
    try:
        tool = tool_by_name(tools, tool_name)
        output = await tool.ainvoke(tool_input)
        trace_item = AgentToolTrace(
            tool_name=tool_name,
            input=tool_input,
            output=json_safe(output),
            status="success",
        )
        trace.append(trace_item)
        await emit_event(callback, "tool.finished", trace_item.model_dump(mode="json"))
        return output
    except Exception as exc:
        trace_item = AgentToolTrace(
            tool_name=tool_name,
            input=tool_input,
            status="error",
            error=str(exc),
        )
        trace.append(trace_item)
        await emit_event(callback, "tool.finished", trace_item.model_dump(mode="json"))
        return None
