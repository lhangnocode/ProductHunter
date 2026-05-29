import { describe, it, expect, vi, beforeEach } from 'vitest';
import { wishlistService } from '../wishlist';
import type { WishListItem } from '../wishlist';

// Mock the global fetch
global.fetch = vi.fn();

describe('wishlistService', () => {
  const mockToken = 'valid-access-token';

  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ============================================================
  // GET WISHLIST
  // ============================================================
  describe('getWishlist', () => {
    it('should fetch wishlist items successfully', async () => {
      const mockWishlist = {
        items: [
          {
            product_id: 'prod-1',
            added_at: '2024-01-15T10:00:00',
            product_name: 'iPhone 15',
            main_image_url: 'https://example.com/image1.jpg'
          },
          {
            product_id: 'prod-2',
            added_at: '2024-01-14T09:30:00',
            product_name: 'MacBook Pro',
            main_image_url: 'https://example.com/image2.jpg'
          }
        ]
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockWishlist
      });

      const result = await wishlistService.getWishlist(mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/wish_lists/'),
        expect.objectContaining({
          headers: { 'Authorization': `Bearer ${mockToken}` }
        })
      );
      expect(result).toHaveLength(2);
      expect(result[0].product_name).toBe('iPhone 15');
    });

    it('should return empty array when wishlist is empty', async () => {
      const mockWishlist = { items: [] };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockWishlist
      });

      const result = await wishlistService.getWishlist(mockToken);

      expect(result).toEqual([]);
    });

    it('should handle response without items property', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      const result = await wishlistService.getWishlist(mockToken);

      expect(result).toEqual([]);
    });

    it('should return empty array on unauthorized access', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401
      });

      const result = await wishlistService.getWishlist('invalid-token');

      expect(result).toEqual([]);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should log error and return empty array on network error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (global.fetch as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      const result = await wishlistService.getWishlist(mockToken);

      expect(result).toEqual([]);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  // ============================================================
  // ADD TO WISHLIST
  // ============================================================
  describe('addToWishlist', () => {
    it('should add product to wishlist successfully', async () => {
      const mockResponse = {
        items: [
          {
            product_id: 'prod-1',
            added_at: '2024-01-15T10:00:00',
            product_name: 'New Product',
            main_image_url: 'https://example.com/image.jpg'
          }
        ]
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await wishlistService.addToWishlist(mockToken, 'prod-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/wish_lists/'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${mockToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ product_id: 'prod-1' })
        })
      );
      expect(result).toHaveLength(1);
      expect(result[0].product_id).toBe('prod-1');
    });

    it('should throw error when adding duplicate product', async () => {
      const errorResponse = {
        detail: 'Product already in wishlist'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorResponse
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.addToWishlist(mockToken, 'prod-1'))
        .rejects
        .toThrow('Product already in wishlist');

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should throw error on unauthorized', async () => {
      const errorResponse = {
        detail: 'Not authenticated'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => errorResponse
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.addToWishlist('invalid-token', 'prod-1'))
        .rejects
        .toThrow('Not authenticated');

      consoleSpy.mockRestore();
    });

    it('should throw error with default message on JSON parse failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Parse error'); }
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.addToWishlist(mockToken, 'prod-1'))
        .rejects
        .toThrow('Thêm vào wishlist thất bại (500)');

      consoleSpy.mockRestore();
    });

    it('should handle response without items property', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      const result = await wishlistService.addToWishlist(mockToken, 'prod-1');

      expect(result).toEqual([]);
    });
  });

  // ============================================================
  // REMOVE FROM WISHLIST
  // ============================================================
  describe('removeFromWishlist', () => {
    it('should remove product from wishlist successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Removed' })
      });

      await wishlistService.removeFromWishlist(mockToken, 'prod-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/wish_lists/prod-1'),
        expect.objectContaining({
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${mockToken}` }
        })
      );
    });

    it('should throw error when product not found in wishlist', async () => {
      const errorResponse = {
        detail: 'Product not in wishlist'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => errorResponse
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.removeFromWishlist(mockToken, 'invalid-prod'))
        .rejects
        .toThrow('Product not in wishlist');

      consoleSpy.mockRestore();
    });

    it('should throw error on unauthorized', async () => {
      const errorResponse = {
        detail: 'Token expired'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => errorResponse
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.removeFromWishlist('expired-token', 'prod-1'))
        .rejects
        .toThrow('Token expired');

      consoleSpy.mockRestore();
    });

    it('should throw error with default message on JSON parse failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Parse error'); }
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(wishlistService.removeFromWishlist(mockToken, 'prod-1'))
        .rejects
        .toThrow('Xóa wishlist thất bại (500)');

      consoleSpy.mockRestore();
    });

    it('should log error on network failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (global.fetch as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(wishlistService.removeFromWishlist(mockToken, 'prod-1'))
        .rejects
        .toThrow();

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });
});
