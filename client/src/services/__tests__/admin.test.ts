import { beforeEach, describe, expect, it, vi } from 'vitest';
import { adminService } from '../admin';

// Mock global fetch
global.fetch = vi.fn();

describe('adminService', () => {
  const MOCK_TOKEN = 'test-token';

  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('User Management', () => {
    it('should fetch users with correct headers', async () => {
      const mockUsers = [
        { id: '1', email: 'a@test.com', full_name: 'Admin', plan: 1, created_at: '2024-01-01' }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers,
      });

      const result = await adminService.getUsers(MOCK_TOKEN);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/admin/users'),
        expect.objectContaining({
          headers: { Authorization: `Bearer ${MOCK_TOKEN}` },
        })
      );
      expect(result).toEqual(mockUsers);
    });

    it('should update user plan with PATCH method', async () => {
      const mockResponse = { id: '1', plan: 1 };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await adminService.updateUserPlan(MOCK_TOKEN, '1', 1);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/admin/users/1/plan'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ plan: 1 }),
        })
      );
    });
  });

  describe('Payment Management', () => {
    it('should fetch payment requests', async () => {
      const mockPayments = [{ id: 'p1', email: 'user@test.com', amount: 50000 }];
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPayments,
      });

      const result = await adminService.getPaymentRequests(MOCK_TOKEN);
      expect(result).toEqual(mockPayments);
    });

    it('should call approve payment endpoint', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success' }),
      });

      await adminService.approvePayment(MOCK_TOKEN, 'pay-123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/admin/payments/pay-123/approve'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('Error Handling', () => {
    it('should throw error detail from backend when response is not ok', async () => {
      const backendError = 'Admin access is required.';
      
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: backendError }),
      });

      // Kiểm tra xem service có ném ra đúng message từ backend không
      await expect(adminService.getUsers(MOCK_TOKEN)).rejects.toThrow(backendError);
    });

    it('should fall back to default error message if no detail provided', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({}), // Không có trường detail
      });

      await expect(adminService.getUsers(MOCK_TOKEN)).rejects.toThrow('Lỗi tải danh sách người dùng');
    });
  });
});