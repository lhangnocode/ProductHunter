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

export interface AdminOverviewCounts {
  products: number;
  platform_products: number;
  platforms: number;
  in_stock_offers: number;
  users: number;
  pending_payments: number;
}

export interface AdminOverviewProduct {
  id: string;
  product_name: string | null;
  normalized_name: string;
  brand: string | null;
  category: string | null;
  main_image_url: string | null;
  offer_count: number;
}

export interface AdminOverviewOffer {
  platform_product_id: string;
  product_id: string | null;
  product_name: string;
  platform_id: number;
  platform_name: string;
  price: number | null;
  original_price: number | null;
  in_stock: boolean;
  url: string;
  last_crawled_at: string | null;
}

export interface AdminOverview {
  counts: AdminOverviewCounts;
  recent_products: AdminOverviewProduct[];
  sample_offers: AdminOverviewOffer[];
}

const ADMIN_OVERVIEW_CACHE_TTL_MS = 60_000;
let adminOverviewCache: { token: string; data: AdminOverview; expiresAt: number } | null = null;

function clearAdminOverviewCache() {
  adminOverviewCache = null;
}

export const adminService = {
  async getOverview(token: string, forceRefresh = false): Promise<AdminOverview> {
    if (
      !forceRefresh &&
      adminOverviewCache &&
      adminOverviewCache.token === token &&
      adminOverviewCache.expiresAt > Date.now()
    ) {
      return adminOverviewCache.data;
    }

    const response = await fetch(`${CONFIG.API_URL}/admin/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Lỗi tải tổng quan dashboard');
    }
    const data = await response.json();
    adminOverviewCache = {
      token,
      data,
      expiresAt: Date.now() + ADMIN_OVERVIEW_CACHE_TTL_MS,
    };
    return data;
  },

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
    clearAdminOverviewCache();
    return response.json();
  },

  async rejectPayment(token: string, paymentId: string) {
    const response = await fetch(`${CONFIG.API_URL}/admin/payments/${paymentId}/reject`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    clearAdminOverviewCache();
    return response.json();
  }
};
