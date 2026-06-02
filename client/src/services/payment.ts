import { CONFIG } from '../config';

export const paymentService = {
  async createPaymentRequest(accessToken: string, amount: number, imageFile: File) {
    // Vì có gửi ảnh, ta dùng FormData
    const formData = new FormData();
    formData.append('amount', amount.toString());
    formData.append('receipt', imageFile); // File ảnh thực tế

    const response = await fetch(`${CONFIG.API_URL}/payments/request`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        // Không set Content-Type để browser tự nhận diện boundary của FormData
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Không thể gửi yêu cầu thanh toán');
    }
    return response.json();
  }
};