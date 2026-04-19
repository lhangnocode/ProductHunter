import { CONFIG } from '../config'

export async function fetchTrendingDeals(): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_URL}/platform_products/platform-products/trending?limit=20`);
  if (!response.ok) throw new Error('Không thể tải Trending Deals');
  return response.json();
}
