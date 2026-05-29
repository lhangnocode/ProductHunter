import { CONFIG } from "../config";

export type AdvisorChatRole = "user" | "assistant";

export interface AdvisorChatMessage {
  role: AdvisorChatRole;
  content: string;
}

export interface AdvisorChatContext {
  active_tab?: string;
  search_query?: string;
  product_id?: string;
}

export interface AdvisorPlatformRecommendation {
  platform: string;
  price: number | null;
  url: string | null;
  in_stock: boolean | null;
}

export interface AdvisorRecommendation {
  product_id: string;
  product_name: string;
  reason: string;
  lowest_price: number | null;
  platforms: AdvisorPlatformRecommendation[];
}

export interface AdvisorSource {
  type: string;
  id: string;
  label: string;
}

export interface AdvisorChatResponse {
  answer: string;
  recommendations: AdvisorRecommendation[];
  sources: AdvisorSource[];
}

export async function sendAdvisorMessage(
  message: string,
  history: AdvisorChatMessage[],
  context: AdvisorChatContext,
): Promise<AdvisorChatResponse> {
  const response = await fetch(`${CONFIG.API_URL}/advisor/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      context,
    }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || "Không thể kết nối ProductHunter Advisor");
  }

  return response.json();
}
