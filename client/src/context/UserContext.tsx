import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authService } from '../services/auth';
import { wishlistService, WishListItem } from '../services/wishlist';

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
  // Wishlist — list of items synced with the backend
  wishlist: WishListItem[];
  wishlistIds: Set<string>;          // for O(1) isWishlisted checks
  isWishlistLoading: boolean;
  toggleWishlist: (productId: string) => Promise<void>;
  clearWishlist: () => Promise<void>;
  // Price alerts (local only — no backend for alerts yet)
  alerts: { productId: string; threshold: number }[];
  setAlert: (productId: string, threshold: number) => void;
  removeAlert: (productId: string) => void;
  clearAlerts: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [wishlist, setWishlist] = useState<WishListItem[]>([]);
  const [isWishlistLoading, setIsWishlistLoading] = useState(false);
  const [alerts, setAlerts] = useState<{ productId: string; threshold: number }[]>(() => {
    const saved = localStorage.getItem('hawk_alerts');
    return saved ? JSON.parse(saved) : [];
  });

  // Derived Set of IDs for fast O(1) lookups
  const wishlistIds = new Set(wishlist.map(item => item.product_id));

  // Load wishlist from the backend
  const loadWishlist = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) { setWishlist([]); return; }
    setIsWishlistLoading(true);
    try {
      const items = await wishlistService.getWishlist(token);
      setWishlist(items);
    } catch {
      setWishlist([]);
    } finally {
      setIsWishlistLoading(false);
    }
  }, []);

  // Restore session on mount
  useEffect(() => {
    const initAuth = async () => {
      // Handle social login tokens in URL
      const urlParams = new URLSearchParams(window.location.search);
      const urlAccessToken = urlParams.get('access_token');
      const urlRefreshToken = urlParams.get('refresh_token');
      if (urlAccessToken && urlRefreshToken) {
        localStorage.setItem('access_token', urlAccessToken);
        localStorage.setItem('refresh_token', urlRefreshToken);
        window.history.replaceState({}, document.title, window.location.pathname);
      }

      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authService.getMe(token);
          setUser(userData);
          // Load wishlist right after we confirm the session is valid
          const items = await wishlistService.getWishlist(token);
          setWishlist(items);
        } catch {
          logout();
        }
      }
      setIsLoadingUser(false);
    };
    initAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync alerts to localStorage
  useEffect(() => {
    localStorage.setItem('hawk_alerts', JSON.stringify(alerts));
  }, [alerts]);

  const setAuthData = async (token: string, userData: User) => {
    localStorage.setItem('access_token', token);
    setUser(userData);
    // Immediately load wishlist for the freshly logged-in user
    try {
      const items = await wishlistService.getWishlist(token);
      setWishlist(items);
    } catch {
      setWishlist([]);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setWishlist([]);
  };

  /**
   * Toggle a product in/out of the wishlist.
   * Performs an optimistic UI update then syncs with the backend.
   */
  const toggleWishlist = async (productId: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('not_logged_in');

    const isInWishlist = wishlistIds.has(productId);

    // --- Optimistic update ---
    if (isInWishlist) {
      setWishlist(prev => prev.filter(i => i.product_id !== productId));
    } else {
      // Add a placeholder so the heart turns red instantly
      setWishlist(prev => [
        { product_id: productId, added_at: new Date().toISOString(), product_name: null, main_image_url: null },
        ...prev,
      ]);
    }

    try {
      if (isInWishlist) {
        await wishlistService.removeFromWishlist(token, productId);
        // No need to refresh; we already removed it optimistically
      } else {
        const items = await wishlistService.addToWishlist(token, productId);
        // Replace with authoritative list from backend (fills in product_name etc.)
        setWishlist(items);
      }
    } catch (err) {
      // Rollback on failure
      await loadWishlist();
      throw err;
    }
  };

  /**
   * Remove every item from the wishlist, one by one against the backend.
   */
  const clearWishlist = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const ids: string[] = wishlist.map(item => item.product_id);
    setWishlist([]); // optimistic clear
    try {
      await Promise.all(ids.map(id => wishlistService.removeFromWishlist(token, id)));
    } catch {
      await loadWishlist(); // reload if something failed
    }
  };

  const setAlert = (productId: string, threshold: number) => {
    setAlerts(prev => {
      const idx = prev.findIndex(a => a.productId === productId);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { productId, threshold };
        return next;
      }
      return [...prev, { productId, threshold }];
    });
  };

  const removeAlert = (productId: string) =>
    setAlerts(prev => prev.filter(a => a.productId !== productId));

  const clearAlerts = () => setAlerts([]);

  return (
    <UserContext.Provider value={{
      user, isLoadingUser, setAuthData, logout,
      wishlist, wishlistIds, isWishlistLoading, toggleWishlist, clearWishlist,
      alerts, setAlert, removeAlert, clearAlerts,
    }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) throw new Error('useUser must be used within a UserProvider');
  return context;
};