import { CONFIG } from '../config'

export interface PriceRecord {
  id: string;
  platform_product_id: string;
  price: number;
  original_price: number | null;
  recorded_at: string;
  is_flash_sale: boolean;
}


export async function searchPlatformProducts(name: string): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_URL}/platform_products/platform-products/search?name=${encodeURIComponent(name)}`);
  if (!response.ok) throw new Error('Search failed');
  return response.json();
}

export async function fetchPriceHistory(platformProductId: string): Promise<PriceRecord[]> {
  const response = await fetch(`${CONFIG.API_URL}/price_record/price-records/${platformProductId}`);
  
  if (!response.ok) {
    throw new Error('Không thể lấy lịch sử giá từ server');
  }
  
  return response.json();
}

export interface PriceAnalysis {
  deal_status: 'extreme' | 'fake' | 'good' | 'slight' | 'stable';
  deal_label: string;
  lowest_ever_price: number;
  avg_price_30d: number;
  current_price: number;
}

export async function fetchPriceAnalysis(id: string, current: number, original: number): Promise<PriceAnalysis> {
  const response = await fetch(
    `${CONFIG.API_URL}/price_record/price-analysis/${id}?current_price=${current}&original_price=${original}`
  );
  if (!response.ok) throw new Error('Analysis failed');
  return response.json();
}

export async function fetchTrendingDeals(): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_URL}/platform_products/platform-products/trending?limit=20`);
  if (!response.ok) throw new Error('Không thể tải Trending Deals');
  return response.json();
}
