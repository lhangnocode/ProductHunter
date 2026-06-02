import { beforeEach, describe, expect, it, vi } from 'vitest';
import { adminService } from '../admin';

global.fetch = vi.fn();

describe('adminService', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('fetches users with bearer auth', async () => {
    const users = [{ id: 'user-1', email: 'buyer@example.com', full_name: 'Buyer', plan: 0, created_at: '2026-01-01T00:00:00Z' }];
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => users,
    });

    const result = await adminService.getUsers('token');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/admin/users'),
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer token' },
      }),
    );
    expect(result).toEqual(users);
  });

  it('updates a user plan', async () => {
    const user = { id: 'user-1', email: 'buyer@example.com', full_name: 'Buyer', plan: 1, created_at: '2026-01-01T00:00:00Z' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => user,
    });

    const result = await adminService.updateUserPlan('token', 'user-1', 1);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/admin/users/user-1/plan'),
      expect.objectContaining({
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer token',
        },
        body: JSON.stringify({ plan: 1 }),
      }),
    );
    expect(result.plan).toBe(1);
  });

  it('throws backend detail when list users fails', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Admin access is required.' }),
    });

    await expect(adminService.getUsers('token')).rejects.toThrow('Admin access is required.');
  });
});
