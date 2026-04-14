import { CONFIG } from '../config';

export interface PriceAlertItem {
  product_id: string;
  target_price: number;
  status: number;
  product_name?: string | null;
  main_image_url?: string | null;
  current_price?: number | null; // Có thể backend trả về hoặc không
}

export const priceAlertService = {
  // Lấy danh sách Alert
  async getAlerts(accessToken: string): Promise<PriceAlertItem[]> {
    const response = await fetch(`${CONFIG.API_URL}/price_alerts/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });
    if (!response.ok) throw new Error('Không thể tải danh sách cảnh báo giá');
    // Giả sử API backend trả về 1 mảng các object. Nếu backend bọc trong object (VD: { items: [...] }) thì đổi thành response.json().then(r => r.items)
    return response.json(); 
  },

  // Thêm/Sửa Alert
  async setAlert(accessToken: string, productId: string, targetPrice: number) {
    const response = await fetch(`${CONFIG.API_URL}/price_alerts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        product_id: productId,
        target_price: targetPrice
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Không thể đặt cảnh báo giá');
    }
    return response.json();
  },

  // Xóa 1 Alert
  async removeAlert(accessToken: string, productId: string) {
    const response = await fetch(`${CONFIG.API_URL}/price_alerts/${productId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });
    if (!response.ok) throw new Error('Không thể xóa cảnh báo giá');
    return response.json();
  }
};