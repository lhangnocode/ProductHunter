import { CONFIG } from '../config'

export interface PriceRecord {
  id: string;
  platform_product_id: string;
  price: number;
  original_price: number | null;
  recorded_at: string;
  is_flash_sale: boolean;
}

export interface PlatformProduct {
  id: string;
  product_id: string;
  platform_id: number;
  raw_name: string;
  current_price: number;
  original_price: number | null;
  url: string;
  in_stock: boolean;
  main_image_url?: string;
  platform?: {
    id: number;
    name: string;
  };
}

export async function searchPlatformProducts(name: string): Promise<any[]> {
  try {
    const response = await fetch(`${CONFIG.API_URL}/products/search?q=${encodeURIComponent(name)}`);
    if (!response.ok) {
      console.error(`Search API failed with status: ${response.status}`);
      return []; 
    }

    const result = await response.json();

    if (Array.isArray(result)) {
      return result;
    }

    if (result && Array.isArray(result.data)) {
      return result.data;
    }

    if (result && Array.isArray(result.items)) {
      return result.items;
    }
    console.warn("API search trả về định dạng lạ:", result);
    return [];
  } catch (error) {
    console.error('Lỗi khi gọi searchPlatformProducts:', error);
    return []; 
  }
}

/**
 * Lấy tất cả các sàn bán sản phẩm này
 */
export async function fetchPlatformProductsByProductId(productId: string): Promise<PlatformProduct[]> {
  try {
    const response = await fetch(
      `${CONFIG.API_URL}/platform_products/platform-products/by-product-id?product_id=${productId}&limit=100`
    );
    
    if (!response.ok) {
      console.error(`Fetch platform products failed with status: ${response.status}`);
      return [];
    }
    
    const result = await response.json();
    if (Array.isArray(result)) {
      return result;
    }
    if (result && Array.isArray(result.data)) {
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('Lỗi khi fetch platform products:', error);
    return [];
  }
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
