import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/auth';

export interface User {
  id: string;
  email: string;
  full_name: string;
  plan: number;
}

interface UserContextType {
  user: User | null;
  isLoadingUser: boolean;
  setAuthData: (token: string, user: User) => void;
  logout: () => void;
  wishlist: string[];
  toggleWishlist: (productId: string) => void;
  clearWishlist: () => void;
  alerts: { productId: string; threshold: number }[];
  setAlert: (productId: string, threshold: number) => void;
  removeAlert: (productId: string) => void;
  clearAlerts: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<{ productId: string; threshold: number }[]>([]);

  // Khôi phục Session khi ứng dụng khởi động
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authService.getMe(token);
          setUser(userData);
        } catch (error) {
          console.error("Session expired:", error);
          logout(); // Xóa token nếu lỗi
        }
      }
      setIsLoadingUser(false);
    };

    initAuth();

    // Load các dữ liệu phụ trợ
    const savedWishlist = localStorage.getItem('hawk_wishlist');
    const savedAlerts = localStorage.getItem('hawk_alerts');
    if (savedWishlist) setWishlist(JSON.parse(savedWishlist));
    if (savedAlerts) setAlerts(JSON.parse(savedAlerts));
  }, []);

  // Sync dữ liệu phụ trợ
  useEffect(() => {
    localStorage.setItem('hawk_wishlist', JSON.stringify(wishlist));
  }, [wishlist]);

  useEffect(() => {
    localStorage.setItem('hawk_alerts', JSON.stringify(alerts));
  }, [alerts]);

  // Hàm được gọi sau khi Login thành công từ AuthModal
  const setAuthData = (token: string, userData: User) => {
    localStorage.setItem('access_token', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const toggleWishlist = (productId: string) => {
    setWishlist(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId) 
        : [...prev, productId]
    );
  };

  const clearWishlist = () => {
    setWishlist([]);
  };

  const setAlert = (productId: string, threshold: number) => {
    setAlerts(prev => {
      const existing = prev.findIndex(a => a.productId === productId);
      if (existing >= 0) {
        const newAlerts = [...prev];
        newAlerts[existing] = { productId, threshold };
        return newAlerts;
      }
      return [...prev, { productId, threshold }];
    });
  };

  const removeAlert = (productId: string) => {
    setAlerts(prev => prev.filter(a => a.productId !== productId));
  };

  const clearAlerts = () => {
    setAlerts([]);
  };

  return (
    <UserContext.Provider value={{ 
      user, isLoadingUser, setAuthData, logout, 
      wishlist, toggleWishlist, clearWishlist,
      alerts, setAlert, removeAlert, clearAlerts
    }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};