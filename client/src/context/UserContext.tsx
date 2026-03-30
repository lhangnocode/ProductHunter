import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  email: string;
  name: string;
}

interface UserContextType {
  user: User | null;
  login: (email: string, name: string) => void;
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
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<{ productId: string; threshold: number }[]>([]);

  // Load from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('hawk_user');
    const savedWishlist = localStorage.getItem('hawk_wishlist');
    const savedAlerts = localStorage.getItem('hawk_alerts');

    if (savedUser) setUser(JSON.parse(savedUser));
    if (savedWishlist) setWishlist(JSON.parse(savedWishlist));
    if (savedAlerts) setAlerts(JSON.parse(savedAlerts));
  }, []);

  // Save to localStorage on changes
  useEffect(() => {
    if (user) localStorage.setItem('hawk_user', JSON.stringify(user));
    else localStorage.removeItem('hawk_user');
  }, [user]);

  useEffect(() => {
    localStorage.setItem('hawk_wishlist', JSON.stringify(wishlist));
  }, [wishlist]);

  useEffect(() => {
    localStorage.setItem('hawk_alerts', JSON.stringify(alerts));
  }, [alerts]);

  const login = (email: string, name: string) => {
    setUser({ email, name });
  };

  const logout = () => {
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
      user, login, logout, 
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
