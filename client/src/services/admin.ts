import { CONFIG } from '../config';

export interface AdminUser {
  id: string;
  email: string;
  full_name?: string | null;
  plan: number;
  created_at: string;
}

export const adminService = {
  async getUsers(accessToken: string): Promise<AdminUser[]> {
    const response = await fetch(`${CONFIG.API_URL}/admin/users`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || 'Không thể tải danh sách người dùng');
    }

    return response.json();
  },

  async updateUserPlan(accessToken: string, userId: string, plan: 0 | 1): Promise<AdminUser> {
    const response = await fetch(`${CONFIG.API_URL}/admin/users/${userId}/plan`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ plan }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || 'Không thể cập nhật gói người dùng');
    }

    return response.json();
  },
};
