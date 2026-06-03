import { beforeEach, describe, expect, it, vi } from "vitest";

import { sendAgentMessage, streamAgentMessage } from "../agent";
import type { AgentChatContext, AgentChatMessage } from "../agent";

global.fetch = vi.fn();

describe("agent service", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("sends a non-streaming agent message", async () => {
    const mockResponse = {
      answer: "Use this product for the customer.",
      recommendations: [],
      sources: [],
      tool_trace: [],
      handoff_required: false,
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const history: AgentChatMessage[] = [
      { role: "user", content: "Find a phone" },
      { role: "assistant", content: "I found phones" },
    ];
    const context: AgentChatContext = {
      active_tab: "agent",
      search_query: "iphone",
    };

    const result = await sendAgentMessage("What should I say?", history, context);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/agent/chat"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );
    const body = JSON.parse((global.fetch as any).mock.calls[0][1].body);
    expect(body.message).toBe("What should I say?");
    expect(body.history).toEqual(history);
    expect(body.context).toEqual(context);
    expect(body.include_tool_trace).toBe(true);
    expect(result.answer).toBe(mockResponse.answer);
  });

  it("parses streamed SSE agent events", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            'event: agent.started\ndata: {"message":"hello"}\n\n' +
              'event: agent.token\ndata: {"content":"Answer"}\n\n' +
              'event: agent.done\ndata: {"answer":"Answer","sources":[]}\n\n',
          ),
        );
        controller.close();
      },
    });
    const events: string[] = [];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const history: AgentChatMessage[] = [
      { role: "user", content: "Find a laptop" },
      { role: "assistant", content: "I found laptop options" },
    ];

    await streamAgentMessage({
      message: "hello",
      history,
      context: { active_tab: "agent" },
      onEvent: ({ event }) => events.push(event),
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/agent/chat/stream"),
      expect.objectContaining({ method: "POST" }),
    );
    const body = JSON.parse((global.fetch as any).mock.calls[0][1].body);
    expect(body.history).toEqual(history);
    expect(events).toEqual(["agent.started", "agent.token", "agent.done"]);
  });
});
