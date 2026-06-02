import { CONFIG } from '../config';

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  plan: number;
  created_at: string;
}

export interface AdminPaymentRequest {
  id: string;
  user_id: string;
  email: string;
  amount: number;
  receipt_url: string;
  status: number; // 0: Pending, 1: Approved, 2: Rejected
  created_at: string;
}

export const adminService = {
  // Users
  async getUsers(token: string): Promise<AdminUser[]> {
    const response = await fetch(`${CONFIG.API_URL}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    
    if (!response.ok) {
      // THÊM LOGIC NÀY:
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Lỗi tải danh sách người dùng');
    }
    return response.json();
  },


  async updateUserPlan(token: string, userId: string, plan: number) {
    const response = await fetch(`${CONFIG.API_URL}/admin/users/${userId}/plan`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ plan }),
    });
    return response.json();
  },

  // Payments
  async getPaymentRequests(token: string): Promise<AdminPaymentRequest[]> {
    const response = await fetch(`${CONFIG.API_URL}/admin/payments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Lỗi tải danh sách thanh toán');
    return response.json();
  },

  async approvePayment(token: string, paymentId: string) {
    const response = await fetch(`${CONFIG.API_URL}/admin/payments/${paymentId}/approve`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.json();
  },

  async rejectPayment(token: string, paymentId: string) {
    const response = await fetch(`${CONFIG.API_URL}/admin/payments/${paymentId}/reject`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.json();
  }
};