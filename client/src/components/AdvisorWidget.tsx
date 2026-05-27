import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  ExternalLink,
  Loader2,
  MessageCircle,
  Plus,
  Send,
  Trash2,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

import {
  AdvisorChatContext,
  AdvisorChatMessage,
  AdvisorRecommendation,
  sendAdvisorMessage,
} from "../services/advisor";

interface AdvisorWidgetProps {
  activeTab: string;
  searchQuery: string;
  productId?: string | null;
  userId?: string | null;
}

interface AdvisorThreadMessage extends AdvisorChatMessage {
  recommendations?: AdvisorRecommendation[];
}

interface AdvisorSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: AdvisorThreadMessage[];
}

const SESSIONS_STORAGE_KEY = "producthunter_advisor_sessions";
const ACTIVE_SESSION_STORAGE_KEY = "producthunter_advisor_active_session";

function createSession(title = "New chat"): AdvisorSession {
  const now = Date.now();
  return {
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    title,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function sessionTitleFromMessage(message: string): string {
  const trimmed = message.trim().replace(/\s+/g, " ");
  return trimmed.length > 34 ? `${trimmed.slice(0, 34)}...` : trimmed || "New chat";
}

function loadSessions(): { sessions: AdvisorSession[]; activeSessionId: string } {
  try {
    const savedSessions = localStorage.getItem(SESSIONS_STORAGE_KEY);
    const parsed = savedSessions ? JSON.parse(savedSessions) : null;
    const sessions = Array.isArray(parsed) && parsed.length > 0 ? parsed : [createSession()];
    const savedActiveId = localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
    const activeSessionId = sessions.some((session) => session.id === savedActiveId)
      ? String(savedActiveId)
      : sessions[0].id;
    return { sessions, activeSessionId };
  } catch {
    const fallback = createSession();
    return { sessions: [fallback], activeSessionId: fallback.id };
  }
}

function resetStoredSessions(): { sessions: AdvisorSession[]; activeSessionId: string } {
  localStorage.removeItem(SESSIONS_STORAGE_KEY);
  localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
  const session = createSession();
  return { sessions: [session], activeSessionId: session.id };
}

function formatPrice(price: number | null): string {
  if (price === null || price === undefined) return "Price unavailable";
  return `${new Intl.NumberFormat("vi-VN").format(price)} VND`;
}

export function AdvisorWidget({ activeTab, searchQuery, productId, userId }: AdvisorWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sessions, setSessions] = useState<AdvisorSession[]>(() => loadSessions().sessions);
  const [activeSessionId, setActiveSessionId] = useState<string>(() => loadSessions().activeSessionId);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const activeSession = sessions.find((session) => session.id === activeSessionId) || sessions[0];
  const messages = activeSession?.messages || [];
  const previousUserIdRef = useRef<string | null | undefined>(userId);

  const context: AdvisorChatContext = useMemo(
    () => ({
      active_tab: activeTab,
      search_query: searchQuery.trim() || undefined,
      product_id: productId || undefined,
    }),
    [activeTab, productId, searchQuery],
  );

  useEffect(() => {
    localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions.slice(0, 12)));
    localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, activeSessionId);
  }, [activeSessionId, sessions]);

  useEffect(() => {
    if (previousUserIdRef.current && !userId) {
      const reset = resetStoredSessions();
      setSessions(reset.sessions);
      setActiveSessionId(reset.activeSessionId);
      setInput("");
      setError(null);
      setIsOpen(false);
    }
    previousUserIdRef.current = userId;
  }, [userId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isOpen, messages, isLoading]);

  const updateActiveSession = (
    updater: (session: AdvisorSession) => AdvisorSession,
  ) => {
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

  const submitMessage = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading || !activeSession) return;

    const userMessage: AdvisorThreadMessage = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage].slice(-12);
    updateActiveSession((session) => ({
      ...session,
      title: session.messages.length === 0 ? sessionTitleFromMessage(trimmed) : session.title,
      updatedAt: Date.now(),
      messages: nextMessages,
    }));
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await sendAdvisorMessage(trimmed, messages.slice(-6), context);
      const assistantMessage: AdvisorThreadMessage = {
        role: "assistant",
        content: response.answer,
        recommendations: response.recommendations,
      };
      updateActiveSession((session) => ({
        ...session,
        updatedAt: Date.now(),
        messages: [...session.messages, assistantMessage].slice(-12),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể kết nối ProductHunter Advisor");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="advisor-widget fixed bottom-5 right-5 z-[70]">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            className="mb-3 flex h-[min(680px,calc(100vh-7rem))] w-[calc(100vw-2.5rem)] max-w-[460px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl shadow-slate-900/15 ring-1 ring-slate-200 dark:bg-slate-950 dark:shadow-black/40 dark:ring-slate-800"
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-primary text-white shadow-lg shadow-brand-primary/20">
                  <Bot size={18} />
                </div>
                <div>
                  <p className="text-sm font-black uppercase tracking-wide text-slate-950 dark:text-white font-display">
                    Advisor
                  </p>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Qwen + ProductHunter
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={startNewSession}
                  className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-900 dark:hover:text-white"
                  aria-label="New advisor chat"
                  title="New chat"
                >
                  <Plus size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-900 dark:hover:text-white"
                  aria-label="Close advisor"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            <div className="flex gap-2 overflow-x-auto border-b border-slate-200 px-3 py-2 dark:border-slate-800">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group flex max-w-[180px] shrink-0 items-center gap-1 rounded-lg ring-1 ${
                    session.id === activeSessionId
                      ? "bg-brand-primary text-white ring-brand-primary"
                      : "bg-slate-50 text-slate-600 ring-slate-200 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-800 dark:hover:bg-slate-800"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setActiveSessionId(session.id);
                      setError(null);
                    }}
                    className="min-w-0 flex-1 truncate px-3 py-2 text-left text-[11px] font-black uppercase tracking-wide"
                    title={session.title}
                  >
                    {session.title}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteSession(session.id)}
                    className={`mr-1 rounded-md p-1 transition-colors ${
                      session.id === activeSessionId
                        ? "text-white/80 hover:bg-white/15 hover:text-white"
                        : "text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30 dark:hover:text-rose-300"
                    }`}
                    aria-label={`Delete ${session.title}`}
                    title="Delete chat"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
              {messages.length === 0 && (
                <div className="rounded-xl bg-slate-50 p-4 text-sm font-medium leading-relaxed text-slate-600 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-800">
                  Ask for a product recommendation, price comparison, or deal check.
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                      message.role === "user"
                        ? "bg-brand-primary text-white"
                        : "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-100"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.recommendations && message.recommendations.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {message.recommendations.slice(0, 3).map((item) => (
                          <div
                            key={item.product_id}
                            className="rounded-xl bg-white p-3 text-slate-900 ring-1 ring-slate-200 dark:bg-slate-950 dark:text-slate-100 dark:ring-slate-800"
                          >
                            <p className="text-xs font-black uppercase tracking-wide font-display">
                              {item.product_name}
                            </p>
                            <p className="mt-1 text-[11px] font-bold text-brand-primary">
                              {formatPrice(item.lowest_price)}
                            </p>
                            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                              {item.reason}
                            </p>
                            {item.platforms[0]?.url && (
                              <a
                                href={item.platforms[0].url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-2 inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider text-brand-primary"
                              >
                                {item.platforms[0].platform}
                                <ExternalLink size={11} />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-2xl bg-slate-100 px-3.5 py-2.5 text-sm font-bold text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                    <Loader2 size={15} className="animate-spin" />
                    Thinking
                  </div>
                </div>
              )}

              {error && (
                <div className="rounded-xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700 ring-1 ring-rose-100 dark:bg-rose-950/30 dark:text-rose-300 dark:ring-rose-900/40">
                  {error}
                </div>
              )}

              <div ref={scrollRef} />
            </div>

            <form onSubmit={submitMessage} className="border-t border-slate-200 p-3 dark:border-slate-800">
              <div className="flex items-end gap-2 rounded-xl bg-slate-100 p-2 ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-brand-primary dark:bg-slate-900 dark:ring-slate-800">
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
                  className="max-h-28 min-h-[38px] flex-1 resize-none bg-transparent px-2 py-2 text-sm font-medium text-slate-900 outline-none placeholder:text-slate-400 dark:text-white"
                  placeholder="Ask ProductHunter..."
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-primary text-white transition-all hover:bg-brand-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Send message"
                >
                  {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-primary text-white shadow-2xl shadow-brand-primary/30 ring-1 ring-white/30 transition-all hover:-translate-y-0.5 hover:bg-brand-primary/90 active:scale-95"
        aria-label="Open advisor"
      >
        {isOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </div>
  );
}
