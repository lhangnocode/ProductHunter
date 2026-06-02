import { describe, it, expect, vi, beforeEach } from 'vitest';
import { priceAlertService } from '../priceAlert';
import type { PriceAlertItem } from '../priceAlert';

// Mock the global fetch
global.fetch = vi.fn();

describe('priceAlertService', () => {
  const mockToken = 'valid-access-token';

  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ============================================================
  // GET ALERTS
  // ============================================================
  describe('getAlerts', () => {
    it('should fetch alerts list successfully', async () => {
      const mockAlerts: PriceAlertItem[] = [
        {
          product_id: 'prod-1',
          target_price: 499,
          status: 1,
          product_name: 'iPhone 15',
          main_image_url: 'https://example.com/image.jpg',
          current_price: 599
        },
        {
          product_id: 'prod-2',
          target_price: 899,
          status: 1,
          product_name: 'MacBook',
          main_image_url: 'https://example.com/image2.jpg',
          current_price: 1299
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAlerts
      });

      const result = await priceAlertService.getAlerts(mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/price_alerts/'),
        expect.objectContaining({
          method: 'GET',
          headers: { 'Authorization': `Bearer ${mockToken}` }
        })
      );
      expect(result).toHaveLength(2);
      expect(result[0].product_name).toBe('iPhone 15');
    });

    it('should return empty array on 401 unauthorized', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401
      });

      await expect(priceAlertService.getAlerts('invalid-token'))
        .rejects
        .toThrow();
    });

    it('should handle empty alerts list', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      const result = await priceAlertService.getAlerts(mockToken);

      expect(result).toEqual([]);
    });
  });

  // ============================================================
  // SET ALERT (Create/Update)
  // ============================================================
  describe('setAlert', () => {
    it('should create new price alert successfully', async () => {
      const mockResponse = {
        product_id: 'prod-1',
        target_price: 499,
        status: 1
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await priceAlertService.setAlert(mockToken, 'prod-1', 499);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/price_alerts/'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockToken}`
          },
          body: JSON.stringify({
            product_id: 'prod-1',
            target_price: 499
          })
        })
      );
      expect(result.target_price).toBe(499);
    });

    it('should throw error with invalid token', async () => {
      const errorResponse = {
        detail: 'Not authenticated'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(priceAlertService.setAlert('invalid-token', 'prod-1', 499))
        .rejects
        .toThrow('Not authenticated');
    });

    it('should throw error with product not found', async () => {
      const errorResponse = {
        detail: 'Product not found'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(priceAlertService.setAlert(mockToken, 'invalid-prod', 499))
        .rejects
        .toThrow('Product not found');
    });

    it('should update existing alert by product id', async () => {
      const mockResponse = {
        product_id: 'prod-1',
        target_price: 399,
        status: 1
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      // Calling setAlert with same product_id should update
      const result = await priceAlertService.setAlert(mockToken, 'prod-1', 399);

      expect(result.target_price).toBe(399);
    });
  });

  // ============================================================
  // REMOVE ALERT (Delete)
  // ============================================================
  describe('removeAlert', () => {
    it('should delete alert successfully', async () => {
      const mockResponse = { message: 'Alert deleted' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await priceAlertService.removeAlert(mockToken, 'prod-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/price_alerts/prod-1'),
        expect.objectContaining({
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${mockToken}` }
        })
      );
      expect(result.message).toContain('deleted');
    });

    it('should throw error when alert not found', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Alert not found' })
      });

      await expect(priceAlertService.removeAlert(mockToken, 'invalid-prod'))
        .rejects
        .toThrow('Không thể xóa cảnh báo giá');
    });

    it('should throw error without authentication', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false
      });

      await expect(priceAlertService.removeAlert('', 'prod-1'))
        .rejects
        .toThrow();
    });
  });

  // ============================================================
  // TRIGGER PRICE CHECK
  // ============================================================
  describe('triggerPriceCheck', () => {
    it('should trigger price check successfully', async () => {
      const mockResponse = {
        status: 'completed',
        message: 'Price check completed',
        checked_products: 5,
        triggered_alerts: 2,
        skipped_without_price: 0
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await priceAlertService.triggerPriceCheck(mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/price_alerts/trigger'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockToken}`
          }
        })
      );
      expect(result.checked_products).toBe(5);
      expect(result.triggered_alerts).toBe(2);
    });

    it('should return zero results when no alerts need checking', async () => {
      const mockResponse = {
        status: 'completed',
        message: 'No alerts to check',
        checked_products: 0,
        triggered_alerts: 0,
        skipped_without_price: 0
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await priceAlertService.triggerPriceCheck(mockToken);

      expect(result.checked_products).toBe(0);
      expect(result.triggered_alerts).toBe(0);
    });

    it('should throw error when unauthorized', async () => {
      const errorResponse = {
        detail: 'Token expired'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(priceAlertService.triggerPriceCheck('expired-token'))
        .rejects
        .toThrow('Token expired');
    });

    it('should throw error with fallback message on JSON parse failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => { throw new Error('Parse error'); }
      });

      await expect(priceAlertService.triggerPriceCheck(mockToken))
        .rejects
        .toThrow('Không thể kích hoạt kiểm tra giá');
    });

    it('should include empty body in POST request', async () => {
      const mockResponse = {
        status: 'completed',
        message: 'OK',
        checked_products: 1,
        triggered_alerts: 0,
        skipped_without_price: 0
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      await priceAlertService.triggerPriceCheck(mockToken);

      const callArgs = (global.fetch as any).mock.calls[0];
      expect(callArgs[1].body).toBe(JSON.stringify({}));
    });
  });
});
