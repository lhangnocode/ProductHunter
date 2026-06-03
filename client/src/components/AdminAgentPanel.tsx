import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  ChevronDown,
  ChevronRight,
  Loader2,
  MessageSquareText,
  Plus,
  Send,
  Trash2,
} from "lucide-react";

import {
  AgentChatContext,
  AgentChatMessage,
  AgentRecommendation,
  AgentSource,
  AgentToolTrace,
  streamAgentMessage,
} from "../services/agent";

interface AgentThreadMessage extends AgentChatMessage {
  recommendations?: AgentRecommendation[];
  sources?: AgentSource[];
  toolTrace?: AgentToolTrace[];
  toolEvents?: AgentToolEvent[];
}

interface AgentToolEvent {
  event: "tool.started" | "tool.finished";
  data: Partial<AgentToolTrace> & { tool_name: string };
}

function ToolEventsPanel({
  events,
  expanded,
  onToggle,
}: {
  events: AgentToolEvent[];
  expanded: boolean;
  onToggle: () => void;
}) {
  const grouped = events.reduce<Record<string, AgentToolEvent[]>>((acc, event) => {
    const key = event.data.tool_name || "unknown";
    acc[key] = acc[key] || [];
    acc[key].push(event);
    return acc;
  }, {});
  const items = Object.entries(grouped).map(([name, list]) => {
    const startEvent = list.find((e) => e.event === "tool.started");
    const endEvent = list.find((e) => e.event === "tool.finished");
    const status = endEvent?.data?.status || (startEvent ? "running" : "success");
    return {
      name,
      status,
      input: startEvent?.data?.input,
      output: endEvent?.data?.output,
      error: endEvent?.data?.error,
    };
  });

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-[11px] font-semibold text-slate-500 dark:text-slate-400"
      >
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-400" />
          Agent tool calls ({items.length})
        </span>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {!expanded ? (
        <div className="mt-2 space-y-1">
          {items.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <span className="truncate font-mono">{item.name}</span>
              <ToolStatusBadge status={item.status} />
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          {items.map((item) => (
            <div
              key={item.name}
              className="rounded-md border border-slate-200/70 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-medium text-slate-700 dark:text-slate-200">
                  {item.name}
                </span>
                <ToolStatusBadge status={item.status} />
              </div>
              {item.input && (
                <div className="mt-2">
                  <p className="text-[10px] font-medium text-slate-400 dark:text-slate-500">Input</p>
                  <pre className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-2 text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {typeof item.input === "string"
                      ? item.input
                      : JSON.stringify(item.input, null, 2)}
                  </pre>
                </div>
              )}
              {item.output != null && (
                <div className="mt-2">
                  <p className="text-[10px] font-medium text-slate-400 dark:text-slate-500">Output</p>
                  <pre className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-2 text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {typeof item.output === "string"
                      ? item.output.length > 500
                        ? `${item.output.slice(0, 500)}...`
                        : item.output
                      : JSON.stringify(item.output, null, 2)}
                  </pre>
                </div>
              )}
              {item.error && (
                <p className="mt-2 text-[10px] text-rose-500">{item.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ToolStatusBadge({ status }: { status?: string }) {
  const normalized = status === "error" ? "error" : status === "running" ? "running" : "success";
  const className =
    normalized === "error"
      ? "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
      : normalized === "running"
        ? "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300"
        : "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400";
  return (
    <span className={`ml-3 rounded-full px-2 py-0.5 text-[10px] ${className}`}>
      {normalized}
    </span>
  );
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
      components={{
        p({ children }) {
          return <p className="mb-2 last:mb-0 leading-6">{children}</p>;
        },
        strong({ children }) {
          return <strong className="font-semibold text-slate-900 dark:text-white">{children}</strong>;
        },
        em({ children }) {
          return <em className="italic">{children}</em>;
        },
        ul({ children }) {
          return <ul className="mb-2 ml-4 list-disc space-y-1">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="mb-2 ml-4 list-decimal space-y-1">{children}</ol>;
        },
        li({ children }) {
          return <li className="leading-6">{children}</li>;
        },
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:decoration-blue-600"
            >
              {children}
            </a>
          );
        },
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const isInline = !match && !className;
          if (isInline) {
            return (
              <code
                className="rounded bg-slate-100 px-1.5 py-0.5 text-[13px] font-mono text-slate-800 dark:bg-slate-800 dark:text-slate-200"
                {...props}
              >
                {children}
              </code>
            );
          }
          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
        pre({ children }) {
          return (
            <pre className="mb-2 overflow-x-auto rounded-lg bg-slate-100 p-3 text-[12px] font-mono dark:bg-slate-800">
              {children}
            </pre>
          );
        },
        blockquote({ children }) {
          return (
            <blockquote className="mb-2 border-l-4 border-slate-300 pl-3 italic text-slate-600 dark:border-slate-600 dark:text-slate-400">
              {children}
            </blockquote>
          );
        },
        h1({ children }) {
          return <h1 className="mb-2 text-lg font-bold">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="mb-2 text-base font-bold">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="mb-1 text-sm font-semibold">{children}</h3>;
        },
        hr() {
          return <hr className="my-3 border-slate-200 dark:border-slate-700" />;
        },
        table({ children }) {
          return (
            <div className="mb-2 overflow-x-auto">
              <table className="min-w-full text-[12px]">{children}</table>
            </div>
          );
        },
        th({ children }) {
          return (
            <th className="border border-slate-200 bg-slate-50 px-2 py-1 text-left font-medium dark:border-slate-700 dark:bg-slate-800">
              {children}
            </th>
          );
        },
        td({ children }) {
          return (
            <td className="border border-slate-200 px-2 py-1 dark:border-slate-700">
              {children}
            </td>
          );
        },
      }}
    >
      {content}
    </Markdown>
  );
}

interface AgentSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: AgentThreadMessage[];
}

const SESSIONS_STORAGE_KEY = "producthunter_admin_agent_sessions";
const ACTIVE_SESSION_STORAGE_KEY = "producthunter_admin_agent_active_session";

function createSession(title = "New agent chat"): AgentSession {
  const now = Date.now();
  return {
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    title,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function loadSessions(): { sessions: AgentSession[]; activeSessionId: string } {
  try {
    const rawSessions = localStorage.getItem(SESSIONS_STORAGE_KEY);
    const parsed = rawSessions ? JSON.parse(rawSessions) : null;
    const sessions = Array.isArray(parsed) && parsed.length > 0 ? parsed : [createSession()];
    const rawActiveId = localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
    const activeSessionId = sessions.some((session) => session.id === rawActiveId)
      ? String(rawActiveId)
      : sessions[0].id;
    return { sessions, activeSessionId };
  } catch {
    const session = createSession();
    return { sessions: [session], activeSessionId: session.id };
  }
}

function titleFromMessage(message: string): string {
  const trimmed = message.trim().replace(/\s+/g, " ");
  return trimmed.length > 36 ? `${trimmed.slice(0, 36)}...` : trimmed || "New agent chat";
}

export function AdminAgentPanel() {
  const loadedSessions = useMemo(() => loadSessions(), []);
  const [sessions, setSessions] = useState<AgentSession[]>(loadedSessions.sessions);
  const [activeSessionId, setActiveSessionId] = useState(loadedSessions.activeSessionId);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const activeSession = sessions.find((session) => session.id === activeSessionId) || sessions[0];
  const messages = activeSession?.messages || [];

  const context: AgentChatContext = useMemo(
    () => ({
      active_tab: "agent",
    }),
    [],
  );

  useEffect(() => {
    localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions.slice(0, 12)));
    localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, activeSessionId);
  }, [activeSessionId, sessions]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  const updateActiveSession = (updater: (session: AgentSession) => AgentSession) => {
    setSessions((current) =>
      current.map((session) =>
        session.id === activeSessionId ? updater(session) : session,
      ),
    );
  };

  const startNewSession = () => {
    const session = createSession();
    setSessions((current) => [session, ...current].slice(0, 12));
    setActiveSessionId(session.id);
    setInput("");
    setError(null);
  };

  const deleteSession = (sessionId: string) => {
    setSessions((current) => {
      const remaining = current.filter((session) => session.id !== sessionId);
      const nextSessions = remaining.length > 0 ? remaining : [createSession()];
      if (sessionId === activeSessionId) {
        setActiveSessionId(nextSessions[0].id);
      }
      return nextSessions;
    });
    setError(null);
  };

  const appendAssistantShell = () => {
    updateActiveSession((session) => ({
      ...session,
      messages: [...session.messages, { role: "assistant" as const, content: "" }].slice(-20),
      updatedAt: Date.now(),
    }));
  };

  const updateLastAssistant = (message: Partial<AgentThreadMessage>) => {
    updateActiveSession((session) => {
      const messagesCopy = [...session.messages];
      const lastIndex = messagesCopy.map((item) => item.role).lastIndexOf("assistant");
      if (lastIndex < 0) return session;
      messagesCopy[lastIndex] = { ...messagesCopy[lastIndex], ...message };
      return {
        ...session,
        messages: messagesCopy.slice(-20),
        updatedAt: Date.now(),
      };
    });
  };

  const appendToolEvent = (toolEvent: AgentToolEvent) => {
    updateActiveSession((session) => {
      const messagesCopy = [...session.messages];
      const lastIndex = messagesCopy.map((item) => item.role).lastIndexOf("assistant");
      if (lastIndex < 0) return session;
      const last = messagesCopy[lastIndex];
      const nextEvents = [...(last.toolEvents || []), toolEvent];
      messagesCopy[lastIndex] = { ...last, toolEvents: nextEvents };
      return { ...session, messages: messagesCopy.slice(-20), updatedAt: Date.now() };
    });
  };

  const submitMessage = async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending || !activeSession) return;

    const userMessage: AgentThreadMessage = { role: "user", content: trimmed };
    const history = messages
      .filter((message) => message.content.trim())
      .map(({ role, content }) => ({ role, content }))
      .slice(-8);

    updateActiveSession((session) => ({
      ...session,
      title: session.messages.length === 0 ? titleFromMessage(trimmed) : session.title,
      messages: [...session.messages, userMessage].slice(-20),
      updatedAt: Date.now(),
    }));
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      appendAssistantShell();
      const abortController = new AbortController();
      abortRef.current = abortController;

      await streamAgentMessage({
        message: trimmed,
        history,
        context,
        signal: abortController.signal,
        onEvent: ({ event, data }) => {
          if (event === "agent.token") {
            const chunk = typeof data.content === "string" ? data.content : "";
            updateActiveSession((session) => {
              const messagesCopy = [...session.messages];
              const lastIndex = messagesCopy.map((item) => item.role).lastIndexOf("assistant");
              if (lastIndex < 0) return session;
              messagesCopy[lastIndex] = {
                ...messagesCopy[lastIndex],
                content: `${messagesCopy[lastIndex].content}${chunk}`,
              };
              return { ...session, messages: messagesCopy, updatedAt: Date.now() };
            });
          }
          if (event === "tool.started" || event === "tool.finished") {
            appendToolEvent({
              event: event as AgentToolEvent["event"],
              data: data as AgentToolEvent["data"],
            });
          }
          if (event === "agent.done") {
            const recommendations = Array.isArray(data.recommendations)
              ? (data.recommendations as unknown as AgentRecommendation[])
              : [];
            const sources = Array.isArray(data.sources)
              ? (data.sources as unknown as AgentSource[])
              : [];
            const toolTrace = Array.isArray(data.tool_trace)
              ? (data.tool_trace as unknown as AgentToolTrace[])
              : [];
            updateLastAssistant({
              content: String(data.answer || ""),
              recommendations,
              sources,
              toolTrace,
            });
          }
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Cannot connect to ProductHunter Agent");
      updateLastAssistant({ content: "Request failed. Please try again." });
    } finally {
      abortRef.current = null;
      setIsSending(false);
    }
  };

  return (
    <div className="grid h-full min-h-0 w-full grid-cols-[300px_minmax(0,1fr)] overflow-hidden bg-slate-50 dark:bg-slate-900">
      <aside className="flex min-h-0 flex-col overflow-y-auto bg-white dark:bg-slate-950 p-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">Local sessions</p>
            <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Agent chats</h3>
          </div>
          <button
            type="button"
            onClick={startNewSession}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700 transition-colors hover:bg-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            aria-label="New agent chat"
            title="New agent chat"
          >
            <Plus size={16} />
          </button>
        </div>

        <div className="space-y-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-center gap-2 rounded-lg p-2 transition-colors ${session.id === activeSessionId
                  ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
            >
              <button
                type="button"
                onClick={() => {
                  setActiveSessionId(session.id);
                  setError(null);
                }}
                className="min-w-0 flex-1 text-left"
              >
                <p className="truncate text-xs font-medium">{session.title}</p>
                <p className={`mt-0.5 text-[11px] ${session.id === activeSessionId ? "text-white/60 dark:text-slate-500" : "text-slate-400"}`}>
                  {session.messages.length} messages
                </p>
              </button>
              <button
                type="button"
                onClick={() => deleteSession(session.id)}
                className={`rounded-md p-1 opacity-0 transition-opacity group-hover:opacity-100 ${session.id === activeSessionId ? "hover:bg-white/10 dark:hover:bg-slate-950/10" : "hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                aria-label="Delete agent chat"
                title="Delete chat"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      <section className="flex min-w-0 min-h-0 flex-col">
        <div className="bg-white dark:bg-slate-950 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
              <Bot size={20} />
            </div>
            <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Telesale Assistant</h3>
          </div>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="flex h-full min-h-[420px] items-center justify-center">
              <div className="max-w-lg text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-white text-slate-700 shadow-sm dark:bg-slate-950 dark:text-slate-200">
                  <MessageSquareText size={28} />
                </div>
                <h3 className="text-xl font-semibold text-slate-950 dark:text-white">Ask a telesale question</h3>
                <p className="mt-2 text-sm text-slate-500">
                  The assistant will search products, compare prices, and prepare sales content for you to use when calling customers.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[78%] rounded-lg px-4 py-3 shadow-sm ${message.role === "user"
                        ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                        : "bg-white text-slate-700 dark:bg-slate-950 dark:text-slate-200"
                      }`}
                  >
                    {message.role === "assistant" && message.content ? (
                      <div className="text-sm">
                        <MarkdownContent content={message.content} />
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap text-sm leading-6">
                        {message.content || (isSending ? "Thinking..." : "")}
                      </p>
                    )}
                    {message.toolEvents && message.toolEvents.length > 0 && (
                      <ToolEventsPanel
                        events={message.toolEvents}
                        expanded={!!expandedTools[index]}
                        onToggle={() =>
                          setExpandedTools((current) => ({
                            ...current,
                            [index]: !current[index],
                          }))
                        }
                      />
                    )}
                  </div>
                </div>
              ))}
              <div ref={scrollRef} />
            </div>
          )}
        </div>

        {error && (
          <div className="mx-6 mb-3 rounded-lg bg-rose-50 px-4 py-3 text-xs font-medium text-rose-600 dark:bg-rose-950/30 dark:text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={submitMessage} className="bg-white p-4 dark:bg-slate-950">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submitMessage();
                }
              }}
              placeholder="Ask what to tell a customer..."
              rows={2}
              className="min-h-[48px] flex-1 resize-none rounded-lg bg-slate-100 px-4 py-3 text-sm outline-none placeholder:text-slate-400 focus:bg-slate-200 dark:bg-slate-900 dark:text-white dark:focus:bg-slate-800"
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              className="flex h-[48px] w-[52px] items-center justify-center rounded-lg bg-slate-950 text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40 dark:bg-white dark:text-slate-950"
              aria-label="Send agent message"
              title="Send"
            >
              {isSending ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
