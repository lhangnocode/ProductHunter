import { CONFIG } from '../config'

export interface PriceRecord {
  id: string;
  platform_product_id: string;
  price: number;
  original_price: number | null;
  recorded_at: string;
  is_flash_sale: boolean;
  productId: String;
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


export async function searchPlatformProducts(productId: string): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_URL}/platform_products/platform-products/by-product-id?product_id=${encodeURIComponent(productId)}`);
  if (!response.ok) throw new Error('Search failed');

  const result = await response.json();
  // backend returns an array; but handle other shapes defensively
  const items = Array.isArray(result) ? result : (result && Array.isArray(result.data) ? result.data : []);

  // Normalize numeric fields (API may return numbers as strings)
  return items.map((it: any) => ({
    ...it,
    current_price: it.current_price !== null && it.current_price !== undefined ? parseFloat(String(it.current_price)) : null,
    original_price: it.original_price !== null && it.original_price !== undefined ? parseFloat(String(it.original_price)) : null,
  }));
}

export async function searchProducts(name: string): Promise<any[]> {
  try {
    const url = `${CONFIG.API_URL}/products/search?q=${encodeURIComponent(name)}`;
    console.debug('[searchProducts] requesting', url);
    const response = await fetch(url);
    console.debug('[searchProducts] status', response.status);
    if (!response.ok) {
      console.error(`Search API failed with status: ${response.status}`);
      return []; 
    }

    const result = await response.json();
    console.debug('[searchProducts] response body', result);

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

  const result = await response.json();
  const items = Array.isArray(result) ? result : (result && Array.isArray(result.data) ? result.data : []);

  // Normalize price fields to numbers and strip non-numeric characters
  return items.map((rec: any) => {
    const safe = (val: any) => {
      if (val === null || val === undefined) return null;
      const parsed = parseFloat(String(val).replace(/[^0-9.-]+/g, ''));
      return Number.isFinite(parsed) ? parsed : null;
    };

    return {
      id: rec.id,
      platform_product_id: rec.platform_product_id || rec.platformProductId || rec.platform_product || null,
      price: safe(rec.price),
      original_price: safe(rec.original_price),
      recorded_at: rec.recorded_at || rec.timestamp || rec.recordedAt,
      is_flash_sale: rec.is_flash_sale || rec.isFlashSale || false,
      productId: rec.product_id || rec.productId || null,
    } as PriceRecord;
  });
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

export async function fetchCompareGroups(q: string): Promise<any[]> {
  try {
    const response = await fetch(`${CONFIG.API_URL}/products/compare?q=${encodeURIComponent(q)}`);
    if (!response.ok) {
      console.error(`Compare API failed with status: ${response.status}`);
      return [];
    }

    const result = await response.json();
    // Expecting { data: [ { id, normalized_name, main_image_url, lowest_price, platforms: [...] } ] }
    const groups = result && Array.isArray(result.data) ? result.data : (Array.isArray(result) ? result : []);
    return groups;
  } catch (error) {
    console.error('Lỗi khi gọi compare API:', error);
    return [];
  }
}