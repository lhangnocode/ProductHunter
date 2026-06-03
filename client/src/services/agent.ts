import { CONFIG } from "../config";

export type AgentChatRole = "user" | "assistant";

export interface AgentChatMessage {
  role: AgentChatRole;
  content: string;
}

export interface AgentChatContext {
  active_tab?: string;
  search_query?: string;
  product_id?: string;
  shop_id?: number;
}

export interface AgentOffer {
  platform_product_id: string;
  platform_id: number;
  platform_name: string;
  price: number | null;
  original_price: number | null;
  in_stock: boolean | null;
  url: string | null;
  last_crawled_at: string | null;
  deal_score?: number | null;
  discount_pct?: number | null;
  deal_reasons?: string[];
  price_trend?: string | null;
}

export interface AgentRecommendation {
  product_id: string;
  product_name: string;
  brand: string | null;
  category: string | null;
  lowest_price: number | null;
  reason: string;
  offers: AgentOffer[];
  deal_score?: number | null;
  value_score?: number | null;
  urgency_cues?: string[];
  trust_warranty_months?: number | null;
  trust_is_authentic?: boolean | null;
  trust_return_days?: number | null;
}

export interface AgentSource {
  type: string;
  id: string;
  label: string;
}

export interface AgentToolTrace {
  tool_name: string;
  input: Record<string, unknown>;
  output?: unknown;
  status: "success" | "error";
  error?: string | null;
}

export interface AgentChatResponse {
  answer: string;
  recommendations: AgentRecommendation[];
  sources: AgentSource[];
  tool_trace: AgentToolTrace[];
  handoff_required: boolean;
  alternatives?: unknown[];
  objection_answers?: unknown[];
  urgency_cues?: string[];
  disclaimer?: string | null;
}

export interface AgentStreamEvent {
  event: string;
  data: Record<string, unknown>;
}

interface AgentStreamOptions {
  message: string;
  history: AgentChatMessage[];
  context: AgentChatContext;
  includeToolTrace?: boolean;
  signal?: AbortSignal;
  onEvent: (event: AgentStreamEvent) => void;
}

async function parseError(response: Response, fallback: string): Promise<Error> {
  const detail = await response.json().catch(() => null);
  return new Error(detail?.detail || fallback);
}

export async function sendAgentMessage(
  message: string,
  history: AgentChatMessage[],
  context: AgentChatContext,
  includeToolTrace = true,
): Promise<AgentChatResponse> {
  const response = await fetch(`${CONFIG.API_URL}/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      context,
      include_tool_trace: includeToolTrace,
    }),
  });

  if (!response.ok) {
    throw await parseError(response, "Cannot connect to ProductHunter Agent");
  }

  return response.json();
}

export async function streamAgentMessage({
  message,
  history,
  context,
  includeToolTrace = true,
  signal,
  onEvent,
}: AgentStreamOptions): Promise<void> {
  const response = await fetch(`${CONFIG.API_URL}/agent/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      context,
      include_tool_trace: includeToolTrace,
    }),
    signal,
  });

  if (!response.ok) {
    throw await parseError(response, "Cannot stream from ProductHunter Agent");
  }

  if (!response.body) {
    throw new Error("Agent stream is not available in this browser");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      const eventLine = lines.find((line) => line.startsWith("event:"));
      const dataLine = lines.find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;

      const event = eventLine.slice("event:".length).trim();
      const rawData = dataLine.slice("data:".length).trim();
      const data = JSON.parse(rawData || "{}");
      onEvent({ event, data });
    }

    if (done) break;
  }
}
