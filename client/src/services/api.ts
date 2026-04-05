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