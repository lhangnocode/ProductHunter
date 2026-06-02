import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
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
        setAlert: vi.fn(),
        removeAlert: vi.fn(),
        triggerPriceCheck: vi.fn(),
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

const AlertTestComponent = ({ productId }: { productId: string }) => {
    const { alerts, setAlert } = useUser();
    const [message, setMessage] = React.useState('');
    return (
        <div>
            <div data-testid="alert-count">{alerts.length}</div>
            <div data-testid="alert-message">{message}</div>
            <button
                data-testid="set-alert-btn"
                onClick={async () => {
                    try {
                        await setAlert(productId, 123000);
                        setMessage('success');
                    } catch (error: any) {
                        setMessage(error.message);
                    }
                }}
            >
                Set Alert
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

    it('blocks a new sixth price alert locally for free users', async () => {
        (authService.getMe as any).mockResolvedValueOnce({ id: '1', email: 'test@example.com', full_name: 'Test', plan: 0 });
        (wishlistService.wishlistService.getWishlist as any).mockResolvedValueOnce([]);
        (priceAlertService.getAlerts as any).mockResolvedValueOnce([
            { product_id: 'prod-1', target_price: 1, status: 0 },
            { product_id: 'prod-2', target_price: 1, status: 0 },
            { product_id: 'prod-3', target_price: 1, status: 0 },
            { product_id: 'prod-4', target_price: 1, status: 0 },
            { product_id: 'prod-5', target_price: 1, status: 0 },
        ]);

        render(<AlertTestComponent productId="prod-6" />, { wrapper: MockProviders });

        await waitFor(() => expect(screen.getByTestId('alert-count')).toHaveTextContent('5'));
        await act(async () => {
            screen.getByTestId('set-alert-btn').click();
        });

        expect(screen.getByTestId('alert-message')).toHaveTextContent('up to 5 products');
        expect(priceAlertService.setAlert).not.toHaveBeenCalled();
    });

    it('allows free users to update an existing alert at the limit', async () => {
        (authService.getMe as any).mockResolvedValueOnce({ id: '1', email: 'test@example.com', full_name: 'Test', plan: 0 });
        (wishlistService.wishlistService.getWishlist as any).mockResolvedValueOnce([]);
        (priceAlertService.getAlerts as any).mockResolvedValueOnce([
            { product_id: 'prod-1', target_price: 1, status: 0 },
            { product_id: 'prod-2', target_price: 1, status: 0 },
            { product_id: 'prod-3', target_price: 1, status: 0 },
            { product_id: 'prod-4', target_price: 1, status: 0 },
            { product_id: 'prod-5', target_price: 1, status: 0 },
        ]);
        (priceAlertService.setAlert as any).mockResolvedValueOnce({ product_id: 'prod-1', target_price: 123000, status: 0 });

        render(<AlertTestComponent productId="prod-1" />, { wrapper: MockProviders });

        await waitFor(() => expect(screen.getByTestId('alert-count')).toHaveTextContent('5'));
        await act(async () => {
            screen.getByTestId('set-alert-btn').click();
        });

        expect(screen.getByTestId('alert-message')).toHaveTextContent('success');
        expect(priceAlertService.setAlert).toHaveBeenCalledWith('fake-token', 'prod-1', 123000);
    });

    it('does not block pro users from adding a sixth price alert locally', async () => {
        (authService.getMe as any).mockResolvedValueOnce({ id: '1', email: 'test@example.com', full_name: 'Test', plan: 1 });
        (wishlistService.wishlistService.getWishlist as any).mockResolvedValueOnce([]);
        (priceAlertService.getAlerts as any).mockResolvedValueOnce([
            { product_id: 'prod-1', target_price: 1, status: 0 },
            { product_id: 'prod-2', target_price: 1, status: 0 },
            { product_id: 'prod-3', target_price: 1, status: 0 },
            { product_id: 'prod-4', target_price: 1, status: 0 },
            { product_id: 'prod-5', target_price: 1, status: 0 },
        ]);
        (priceAlertService.setAlert as any).mockResolvedValueOnce({ product_id: 'prod-6', target_price: 123000, status: 0 });

        render(<AlertTestComponent productId="prod-6" />, { wrapper: MockProviders });

        await waitFor(() => expect(screen.getByTestId('alert-count')).toHaveTextContent('5'));
        await act(async () => {
            screen.getByTestId('set-alert-btn').click();
        });

        expect(screen.getByTestId('alert-message')).toHaveTextContent('success');
        expect(priceAlertService.setAlert).toHaveBeenCalledWith('fake-token', 'prod-6', 123000);
    });
});
