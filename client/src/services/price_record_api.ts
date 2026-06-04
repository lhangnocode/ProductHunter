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
  platform_product_id?: string;
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

export async function fetchPlatformProductByPlatformProductId(platformProductId: string): Promise<PlatformProduct | null> {
  try {
    const response = await fetch(
      `${CONFIG.API_URL}/platform_products/platform-products/by-platform-product-id/${encodeURIComponent(platformProductId)}`
    );

    if (!response.ok) {
      console.error(`Fetch platform product failed with status: ${response.status}`);
      return null;
    }

    const item = await response.json();
    return {
      ...item,
      platform_product_id: item.platform_product_id ?? item.id,
      current_price: item.current_price != null ? parseFloat(String(item.current_price)) : null,
      original_price: item.original_price != null ? parseFloat(String(item.original_price)) : null,
    };
  } catch (error) {
    console.error('Lỗi khi fetch platform product:', error);
    return null;
  }
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

export interface SearchResponse {
  items: any[];
  page: number;
  size: number;
  total_elements: number;
  total_pages: number;
}

export async function searchProducts(
  name: string,
  page = 1,
  size = 24,
): Promise<SearchResponse> {
  try {
    const url = `${CONFIG.API_URL}/products/search?q=${encodeURIComponent(name)}&page=${page}&limit=${size}`;
    console.debug("[searchProducts] requesting", url);
    const response = await fetch(url);
    console.debug("[searchProducts] status", response.status);
    if (!response.ok) {
      console.error(`Search API failed with status: ${response.status}`);
      return { items: [], page, size, total_elements: 0, total_pages: 0 };
    }

    const result = await response.json();
    console.debug("[searchProducts] response body", result);

    // Backend may return a paged envelope: { page, size, total_elements, total_pages, data: [...] }
    const items = Array.isArray(result)
      ? result
      : Array.isArray(result.data)
      ? result.data
      : Array.isArray(result.items)
      ? result.items
      : [];

    const pageNum = Number(result.page ?? result.page_number ?? result.current_page ?? page) || page;
    const pageSize = Number(result.size ?? result.page_size ?? result.limit ?? size) || size;
    const totalElements = Number(result.total_elements ?? result.total ?? result.total_results ?? 0) || 0;
    const totalPages = Number(result.total_pages ?? result.totalPages ?? Math.ceil(totalElements / pageSize)) || 0;

    return {
      items,
      page: pageNum,
      size: pageSize,
      total_elements: totalElements,
      total_pages: totalPages,
    };
  } catch (error) {
    console.error("Lỗi khi gọi searchProducts:", error);
    return { items: [], page, size, total_elements: 0, total_pages: 0 };
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
  avg_price_60d: number;
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
