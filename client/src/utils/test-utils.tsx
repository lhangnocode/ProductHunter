import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { LanguageProvider } from '../context/LanguageContext';
import { ThemeProvider } from '../context/ThemeContext';
import { ToastProvider } from '../components/Toast';
import { UserContext } from '../context/UserContext';
import { vi } from 'vitest';

/**
 * A custom wrapper that provides all necessary contexts for components.
 * This avoids repeating the MockProviders block in every test file.
 */
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <LanguageProvider>
      <ThemeProvider>
        <ToastProvider>
          <UserContext.Provider value={{
            user: null, 
            isLoadingUser: false,
            setAuthData: vi.fn(), 
            logout: vi.fn(),
            wishlist: [],
            wishlistIds: new Set(),
            isWishlistLoading: false,
            toggleWishlist: vi.fn(),
            clearWishlist: vi.fn(),
            alerts: [],
            alertIds: new Set(),
            isAlertsLoading: false,
            setAlert: vi.fn(),
            removeAlert: vi.fn(),
            clearAlerts: vi.fn()
          }}>
            {children}
          </UserContext.Provider>
        </ToastProvider>
      </ThemeProvider>
    </LanguageProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
