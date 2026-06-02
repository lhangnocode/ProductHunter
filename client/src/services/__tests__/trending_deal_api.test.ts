import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchTrendingDeals } from '../trending_deal_api';

// Mock the global fetch
global.fetch = vi.fn();

describe('trending_deal_api', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ============================================================
  // FETCH TRENDING DEALS
  // ============================================================
  describe('fetchTrendingDeals', () => {
    it('should fetch trending deals successfully', async () => {
      const mockDeals = [
        {
          id: '1',
          product_id: 'prod-1',
          platform_id: 1,
          raw_name: 'iPhone 15 Pro',
          current_price: 999,
          original_price: 1099,
          url: 'https://example.com/phone',
          in_stock: true,
          main_image_url: 'https://example.com/image1.jpg'
        },
        {
          id: '2',
          product_id: 'prod-2',
          platform_id: 2,
          raw_name: 'Samsung 65" TV',
          current_price: 599,
          original_price: 799,
          url: 'https://example.com/tv',
          in_stock: true,
          main_image_url: 'https://example.com/image2.jpg'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeals
      });

      const result = await fetchTrendingDeals();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/platform_products/platform-products/trending')
      );
      expect(result).toHaveLength(2);
      expect(result[0].raw_name).toBe('iPhone 15 Pro');
      expect(result[1].current_price).toBe(599);
    });

    it('should include limit parameter in request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      await fetchTrendingDeals();

      const callArgs = (global.fetch as any).mock.calls[0];
      expect(callArgs[0]).toContain('limit=20');
    });

    it('should handle empty deals list', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      const result = await fetchTrendingDeals();

      expect(result).toEqual([]);
    });

    it('should throw error when API returns 404', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      await expect(fetchTrendingDeals())
        .rejects
        .toThrow('Không thể tải Trending Deals');
    });

    it('should throw error when API returns 500', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(fetchTrendingDeals())
        .rejects
        .toThrow('Không thể tải Trending Deals');
    });

    it('should throw error on network failure', async () => {
      (global.fetch as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(fetchTrendingDeals())
        .rejects
        .toThrow();
    });

    it('should parse multiple deals with varying data', async () => {
      const mockDeals = [
        {
          id: '1',
          product_id: 'prod-1',
          platform_id: 1,
          raw_name: 'Item 1',
          current_price: 100,
          original_price: 150,
          url: 'https://example.com/1',
          in_stock: true,
          main_image_url: 'https://example.com/1.jpg'
        },
        {
          id: '2',
          product_id: 'prod-2',
          platform_id: 2,
          raw_name: 'Item 2',
          current_price: 200,
          original_price: null,
          url: 'https://example.com/2',
          in_stock: false,
          main_image_url: null
        },
        {
          id: '3',
          product_id: 'prod-3',
          platform_id: 3,
          raw_name: 'Item 3',
          current_price: 50,
          original_price: 75,
          url: 'https://example.com/3',
          in_stock: true,
          main_image_url: 'https://example.com/3.jpg'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeals
      });

      const result = await fetchTrendingDeals();

      expect(result).toHaveLength(3);
      expect(result[0].original_price).toBe(150);
      expect(result[1].original_price).toBeNull();
      expect(result[1].in_stock).toBe(false);
      expect(result[2].main_image_url).toBe('https://example.com/3.jpg');
    });

    it('should handle deals with platform information', async () => {
      const mockDeals = [
        {
          id: '1',
          product_id: 'prod-1',
          platform_id: 1,
          raw_name: 'Product on Platform',
          current_price: 299,
          original_price: 399,
          url: 'https://example.com/product',
          in_stock: true,
          main_image_url: 'https://example.com/image.jpg',
          platform: {
            id: 1,
            name: 'Amazon'
          }
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeals
      });

      const result = await fetchTrendingDeals();

      expect(result[0].platform).toBeDefined();
      expect(result[0].platform.name).toBe('Amazon');
    });

    it('should return max 20 deals by default', async () => {
      const mockDeals = Array.from({ length: 20 }, (_, i) => ({
        id: `${i}`,
        product_id: `prod-${i}`,
        platform_id: 1,
        raw_name: `Product ${i}`,
        current_price: 100 + i * 10,
        original_price: 150 + i * 10,
        url: `https://example.com/${i}`,
        in_stock: true,
        main_image_url: `https://example.com/${i}.jpg`
      }));

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeals
      });

      const result = await fetchTrendingDeals();

      expect(result).toHaveLength(20);
    });
  });
});
