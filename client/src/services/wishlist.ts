import { CONFIG } from '../config';

export interface WishListItem {
  product_id: string;
  added_at: string;
  product_name: string | null;
  main_image_url: string | null;
}

const BASE = `${CONFIG.API_URL}/wish_lists`;

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export const wishlistService = {
  async getWishlist(token: string): Promise<WishListItem[]> {
    try {
      const res = await fetch(`${CONFIG.API_URL}/wish_lists/`, {
        headers: authHeader(token),
      });
      if (!res.ok) {
        console.error(`Wishlist GET failed: ${res.status}`);
        return [];
      }
      const data = await res.json();
      return data.items ?? [];
    } catch (error) {
      console.error('Lỗi khi tải wishlist:', error);
      return [];
    }
  },

  async addToWishlist(token: string, productId: string): Promise<WishListItem[]> {
    try {
      const res = await fetch(`${CONFIG.API_URL}/wish_lists/`, {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Thêm vào wishlist thất bại (${res.status})`);
      }
      const data = await res.json();
      return data.items ?? [];
    } catch (error) {
      console.error('Lỗi khi thêm wishlist:', error);
      throw error; // re-throw để UI hiển thị toast lỗi
    }
  },

  async removeFromWishlist(token: string, productId: string): Promise<void> {
    try {
      const res = await fetch(`${CONFIG.API_URL}/wish_lists/${productId}`, {
        method: 'DELETE',
        headers: authHeader(token),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Xóa wishlist thất bại (${res.status})`);
      }
    } catch (error) {
      console.error('Lỗi khi xóa wishlist:', error);
      throw error; // re-throw để UI hiển thị toast lỗi
    }
  },
};
