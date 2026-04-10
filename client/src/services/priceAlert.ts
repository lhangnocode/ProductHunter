// src/services/priceAlert.ts
import { CONFIG } from '../config';

export const priceAlertService = {
  async setAlert(accessToken: string, productId: string, targetPrice: number) {
    const response = await fetch(`${CONFIG.API_URL}/price_alerts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`, // API yêu cầu current_user
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
  }
};