import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { UserContext, UserProvider, useUser } from '../UserContext';
import { ToastProvider } from '../../components/Toast';
import React from 'react';
import * as wishlistService from '../../services/wishlist';
import { authService } from '../../services/auth';
import { priceAlertService } from '../../services/priceAlert';

// Mock the wishlistService directly
vi.mock('../../services/wishlist', () => ({
    wishlistService: {
        getWishlist: vi.fn(),
        addToWishlist: vi.fn(),
        removeFromWishlist: vi.fn(),
    }
}));

vi.mock('../../services/auth', () => ({
    authService: {
        getMe: vi.fn(),
    }
}));

vi.mock('../../services/priceAlert', () => ({
    priceAlertService: {
        getAlerts: vi.fn(),
    }
}));

const TestComponent = () => {
    const { wishlist, toggleWishlist } = useUser();
    return (
        <div>
            <div data-testid="wishlist-count">{wishlist.length}</div>
            <button 
                data-testid="toggle-btn"
                onClick={() => toggleWishlist('prod-123')}
            >
                Toggle
            </button>
        </div>
    );
};

const MockProviders = ({ children }: { children: React.ReactNode }) => (
    <ToastProvider>
        <UserProvider>
            {children}
        </UserProvider>
    </ToastProvider>
);

describe('UserContext', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        localStorage.clear();
        localStorage.setItem('access_token', 'fake-token');
    });

    it('adds product optimistically when toggling', async () => {
        // Setup initial empty responses
        (authService.getMe as any).mockResolvedValueOnce({ id: '1', email: 'test@example.com', full_name: 'Test', plan: 1 });
        (priceAlertService.getAlerts as any).mockResolvedValueOnce([]);
        (wishlistService.wishlistService.getWishlist as any).mockResolvedValueOnce([]);
        (wishlistService.wishlistService.addToWishlist as any).mockResolvedValueOnce([{ product_id: 'prod-123', product_name: 'Real Name' }]);

        render(<TestComponent />, { wrapper: MockProviders });
        
        // Wait for initial load if any
        await act(async () => {
           await new Promise(r => setTimeout(r, 0));
        });

        const btn = screen.getByTestId('toggle-btn');
        
        // Before clicking
        expect(screen.getByTestId('wishlist-count')).toHaveTextContent('0');

        // Click to toggle
        await act(async () => {
            btn.click();
        });

        // After clicking, it should be 1 optimistically
        expect(screen.getByTestId('wishlist-count')).toHaveTextContent('1');
        expect(wishlistService.wishlistService.addToWishlist).toHaveBeenCalledWith('fake-token', 'prod-123');
    });
});
