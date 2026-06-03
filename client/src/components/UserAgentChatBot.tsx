import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  ExternalLink,
  Loader2,
  MessageCircle,
  Send,
  Trash2,
  X,
} from "lucide-react";

import {
  AgentChatContext,
  AgentChatMessage,
  AgentRecommendation,
  AgentSource,
  streamAgentMessage,
} from "../services/agent";

interface UserAgentChatBotProps {
  activeTab: string;
  searchQuery: string;
  productId?: string | null;
  userId?: string | null;
}

interface UserAgentMessage extends AgentChatMessage {
  recommendations?: AgentRecommendation[];
  sources?: AgentSource[];
}

const STORAGE_KEY = "producthunter_user_agent_chat";

function loadMessages(): UserAgentMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    return Array.isArray(parsed) ? parsed.slice(-20) : [];
  } catch {
    return [];
  }
}

function formatPrice(price: number | null | undefined): string {
  if (price === null || price === undefined) return "Chưa cập nhật giá";
  return `${new Intl.NumberFormat("vi-VN").format(price)}đ`;
}

function ShoppingMarkdown({ content }: { content: string }) {
  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
      components={{
        p({ children }) {
          return <p className="mb-2 last:mb-0 leading-6">{children}</p>;
        },
        strong({ children }) {
          return <strong className="font-semibold text-slate-950 dark:text-white">{children}</strong>;
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
              className="break-words text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:decoration-blue-600"
            >
              {children}
            </a>
          );
        },
        code({ children }) {
          return (
            <code className="rounded bg-slate-100 px-1 py-0.5 text-[12px] font-mono dark:bg-slate-800">
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </Markdown>
  );
}

function ShoppingLoadingIndicator() {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
      <Loader2 className="animate-spin" size={15} />
      <span>Đang tìm dữ liệu sản phẩm</span>
      <span className="flex gap-0.5" aria-hidden="true">
        <span className="h-1 w-1 animate-pulse rounded-full bg-slate-400 [animation-delay:0ms]" />
        <span className="h-1 w-1 animate-pulse rounded-full bg-slate-400 [animation-delay:120ms]" />
        <span className="h-1 w-1 animate-pulse rounded-full bg-slate-400 [animation-delay:240ms]" />
      </span>
    </div>
  );
}

export function UserAgentChatBot({
  activeTab,
  searchQuery,
  productId,
  userId,
}: UserAgentChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<UserAgentMessage[]>(() => loadMessages());
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const context: AgentChatContext = useMemo(
    () => ({
      active_tab: `user_chatbot:${activeTab}`,
      search_query: searchQuery.trim() || undefined,
      product_id: productId || undefined,
    }),
    [activeTab, productId, searchQuery],
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-20)));
  }, [messages]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isOpen, messages, isSending]);

  useEffect(() => {
    if (!userId) return;
    setError(null);
  }, [userId]);

  const updateLastAssistant = (message: Partial<UserAgentMessage>) => {
    setMessages((current) => {
      const next = [...current];
      const lastIndex = next.map((item) => item.role).lastIndexOf("assistant");
      if (lastIndex < 0) return current;
      next[lastIndex] = { ...next[lastIndex], ...message };
      return next.slice(-20);
    });
  };

  const resetChat = () => {
    abortRef.current?.abort();
    setMessages([]);
    setInput("");
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const submitMessage = async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const history = messages
      .filter((message) => message.content.trim())
      .map(({ role, content }) => ({ role, content }))
      .slice(-8);

    setMessages((current) => [
      ...current,
      { role: "user" as const, content: trimmed },
      { role: "assistant" as const, content: "" },
    ].slice(-20));
    setInput("");
    setError(null);
    setIsSending(true);

    const abortController = new AbortController();
    abortRef.current = abortController;

    try {
      await streamAgentMessage({
        message: trimmed,
        history,
        context,
        includeToolTrace: false,
        signal: abortController.signal,
        onEvent: ({ event, data }) => {
          if (event === "agent.token") {
            const chunk = typeof data.content === "string" ? data.content : "";
            setMessages((current) => {
              const next = [...current];
              const lastIndex = next.map((item) => item.role).lastIndexOf("assistant");
              if (lastIndex < 0) return current;
              const currentContent = next[lastIndex].content;
              next[lastIndex] = {
                ...next[lastIndex],
                content: `${currentContent}${currentContent ? " " : ""}${chunk}`,
              };
              return next.slice(-20);
            });
          }

          if (event === "agent.done") {
            updateLastAssistant({
              content: String(data.answer || ""),
              recommendations: Array.isArray(data.recommendations)
                ? (data.recommendations as unknown as AgentRecommendation[])
                : [],
              sources: Array.isArray(data.sources)
                ? (data.sources as unknown as AgentSource[])
                : [],
            });
          }
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Không thể kết nối trợ lý mua sắm");
      updateLastAssistant({ content: "Mình chưa kết nối được với trợ lý. Bạn thử lại sau nhé." });
    } finally {
      abortRef.current = null;
      setIsSending(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-[70]">
      {isOpen && (
        <div className="mb-3 flex h-[min(620px,calc(100vh-7rem))] w-[calc(100vw-2.5rem)] max-w-[390px] flex-col overflow-hidden rounded-xl bg-white shadow-2xl shadow-slate-950/20 dark:bg-slate-950 dark:shadow-black/40">
          <div className="flex items-center justify-between bg-white px-4 py-3 dark:bg-slate-950">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                <Bot size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-950 dark:text-white">Shopping Assistant</p>
                <p className="text-[11px] text-slate-500">ProductHunter agent</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={resetChat}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-900 dark:hover:text-white"
                aria-label="Clear shopping assistant chat"
                title="Clear chat"
              >
                <Trash2 size={15} />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-900 dark:hover:text-white"
                aria-label="Close shopping assistant"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto bg-slate-50 p-4 dark:bg-slate-900">
            {messages.length === 0 ? (
              <div className="flex h-full min-h-[300px] items-center justify-center text-center">
                <div>
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-white text-slate-700 shadow-sm dark:bg-slate-950 dark:text-slate-200">
                    <MessageCircle size={24} />
                  </div>
                  <p className="text-sm font-semibold text-slate-950 dark:text-white">Hỏi trợ lý mua sắm</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">
                    Mình có thể gợi ý sản phẩm, so sánh giá và nhắc những điểm cần kiểm tra trước khi mua.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[86%] rounded-xl px-3 py-2 text-sm leading-6 ${
                        message.role === "user"
                          ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                          : "bg-white text-slate-700 shadow-sm dark:bg-slate-950 dark:text-slate-200"
                      }`}
                    >
                      {message.role === "assistant" && !message.content && isSending ? (
                        <ShoppingLoadingIndicator />
                      ) : message.role === "assistant" && message.content ? (
                        <ShoppingMarkdown content={message.content} />
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                      {message.recommendations && message.recommendations.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {message.recommendations.slice(0, 2).map((recommendation) => (
                            <div key={recommendation.product_id} className="rounded-lg bg-slate-50 p-2 dark:bg-slate-900">
                              <p className="text-xs font-semibold text-slate-950 dark:text-white">
                                {recommendation.product_name}
                              </p>
                              <p className="mt-1 text-[11px] text-slate-500">
                                {formatPrice(recommendation.lowest_price)}
                              </p>
                              {recommendation.offers[0]?.url && (
                                <a
                                  href={recommendation.offers[0].url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-slate-700 hover:underline dark:text-slate-300"
                                >
                                  <ExternalLink size={12} />
                                  {recommendation.offers[0].platform_name}
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={scrollRef} />
              </div>
            )}
          </div>

          {error && (
            <div className="bg-rose-50 px-4 py-2 text-xs font-medium text-rose-600 dark:bg-rose-950/40 dark:text-rose-300">
              {error}
            </div>
          )}

          <form onSubmit={submitMessage} className="bg-white p-3 dark:bg-slate-950">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    submitMessage();
                  }
                }}
                rows={1}
                placeholder="Bạn muốn tìm sản phẩm gì?"
                className="min-h-[42px] flex-1 resize-none rounded-lg bg-slate-100 px-3 py-2.5 text-sm outline-none placeholder:text-slate-400 focus:bg-slate-200 dark:bg-slate-900 dark:text-white dark:focus:bg-slate-800"
              />
              <button
                type="submit"
                disabled={!input.trim() || isSending}
                className="flex h-[42px] w-[46px] items-center justify-center rounded-lg bg-slate-950 text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-white dark:text-slate-950"
                aria-label="Send shopping assistant message"
                title="Send"
              >
                {isSending ? <Loader2 className="animate-spin" size={17} /> : <Send size={17} />}
              </button>
            </div>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-950 text-white shadow-xl shadow-slate-950/20 transition-transform active:scale-95 dark:bg-white dark:text-slate-950"
        aria-label="Open shopping assistant"
        title="Shopping assistant"
      >
        {isOpen ? <X size={22} /> : <Bot size={22} />}
      </button>
    </div>
  );
}
