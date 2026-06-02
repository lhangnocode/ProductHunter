// src/services/auth.ts
import { CONFIG } from '../config'
// Chỉnh sửa URL này thành URL Backend FastAPI của bạn
const API_URL = CONFIG.API_URL

export const authService = {
  // Đăng nhập: FastAPI OAuth2PasswordRequestForm yêu cầu content-type là x-www-form-urlencoded
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email); // FastAPI quy định field name là username
    formData.append('password', password);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Đăng nhập thất bại');
    }

    return response.json(); // Trả về { access_token, refresh_token, token_type }
  },

  // Đăng ký
  async register(email: string, password: string, fullName: string) {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Đăng ký thất bại');
    }

    return response.json();
  },

  async forgotPassword(email: string) {
    const response = await fetch(`${API_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Gửi yêu cầu đặt lại mật khẩu thất bại');
    }

    return response.json();
  },

  async resetPassword(token: string, newPassword: string) {
    const response = await fetch(`${API_URL}/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, new_password: newPassword }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Đặt lại mật khẩu thất bại');
    }

    return response.json();
  },

  // Lấy thông tin user hiện tại (Sử dụng Access Token)
  async getMe(accessToken: string) {
    const response = await fetch(`${API_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) throw new Error('Token không hợp lệ hoặc đã hết hạn');
    return response.json();
  }
};
