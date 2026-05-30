import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ToastProvider } from '../../components/Toast';
import { UserProvider, useUser } from '../UserContext';
import { authService } from '../../services/auth';
import { wishlistService } from '../../services/wishlist';
import { priceAlertService } from '../../services/priceAlert';

vi.mock('../../services/auth', () => ({
  authService: {
    getMe: vi.fn(),
  },
}));

vi.mock('../../services/wishlist', () => ({
  wishlistService: {
    getWishlist: vi.fn(),
    addToWishlist: vi.fn(),
    removeFromWishlist: vi.fn(),
  },
}));

vi.mock('../../services/priceAlert', () => ({
  priceAlertService: {
    getAlerts: vi.fn(),
    setAlert: vi.fn(),
    removeAlert: vi.fn(),
    triggerPriceCheck: vi.fn(),
  },
}));

const mockedGetMe = vi.mocked(authService.getMe);
const mockedGetWishlist = vi.mocked(wishlistService.getWishlist);
const mockedGetAlerts = vi.mocked(priceAlertService.getAlerts);
const mockedSetAlert = vi.mocked(priceAlertService.setAlert);
const mockedRemoveAlert = vi.mocked(priceAlertService.removeAlert);

function ContextProbe() {
  const {
    user,
    isLoadingUser,
    wishlist,
    wishlistIds,
    alerts,
    alertIds,
    setAlert,
    removeAlert,
    logout,
  } = useUser();

  return (
    <div>
      <div data-testid="loading">{String(isLoadingUser)}</div>
      <div data-testid="email">{user?.email ?? 'anonymous'}</div>
      <div data-testid="wishlist-count">{wishlist.length}</div>
      <div data-testid="wishlist-has-product-1">{String(wishlistIds.has('product-1'))}</div>
      <div data-testid="alert-count">{alerts.length}</div>
      <div data-testid="alert-has-product-1">{String(alertIds.has('product-1'))}</div>
      <div data-testid="first-alert-target">{alerts[0]?.target_price ?? 'none'}</div>
      <button type="button" onClick={() => setAlert('product-2', 15000000)}>
        Set alert
      </button>
      <button type="button" onClick={() => removeAlert('product-1')}>
        Remove alert
      </button>
      <button type="button" onClick={logout}>
        Logout
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <UserProvider>
        <ContextProbe />
      </UserProvider>
    </ToastProvider>,
  );
}

describe('UserContext integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('access_token', 'client-token');
  });

  it('restores an authenticated session and hydrates wishlist and alerts from services', async () => {
    mockedGetMe.mockResolvedValueOnce({
      id: 'user-1',
      email: 'buyer@example.com',
      full_name: 'Buyer',
      plan: 1,
    });
    mockedGetWishlist.mockResolvedValueOnce([
      {
        product_id: 'product-1',
        product_name: 'iPhone 15',
        main_image_url: 'https://example.com/iphone.jpg',
        added_at: '2026-05-30T00:00:00.000Z',
      },
    ]);
    mockedGetAlerts.mockResolvedValueOnce([
      {
        product_id: 'product-1',
        target_price: 18000000,
        status: 0,
        product_name: 'iPhone 15',
        main_image_url: 'https://example.com/iphone.jpg',
      },
    ]);

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(mockedGetMe).toHaveBeenCalledWith('client-token');
    expect(mockedGetWishlist).toHaveBeenCalledWith('client-token');
    expect(mockedGetAlerts).toHaveBeenCalledWith('client-token');
    expect(screen.getByTestId('email')).toHaveTextContent('buyer@example.com');
    expect(screen.getByTestId('wishlist-count')).toHaveTextContent('1');
    expect(screen.getByTestId('wishlist-has-product-1')).toHaveTextContent('true');
    expect(screen.getByTestId('alert-count')).toHaveTextContent('1');
    expect(screen.getByTestId('alert-has-product-1')).toHaveTextContent('true');
  });

  it('updates alerts through the provider and clears client state on logout', async () => {
    mockedGetMe.mockResolvedValueOnce({
      id: 'user-1',
      email: 'buyer@example.com',
      full_name: 'Buyer',
      plan: 1,
    });
    mockedGetWishlist.mockResolvedValueOnce([]);
    mockedGetAlerts.mockResolvedValueOnce([
      {
        product_id: 'product-1',
        target_price: 18000000,
        status: 0,
        product_name: 'iPhone 15',
        main_image_url: null,
      },
    ]);
    mockedSetAlert.mockResolvedValueOnce({
      product_id: 'product-2',
      target_price: 15000000,
      status: 0,
      product_name: 'Galaxy S24',
      main_image_url: null,
    });
    mockedRemoveAlert.mockResolvedValueOnce({ success: true });

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('alert-count')).toHaveTextContent('1');
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Set alert'));
    });

    expect(mockedSetAlert).toHaveBeenCalledWith('client-token', 'product-2', 15000000);
    expect(screen.getByTestId('alert-count')).toHaveTextContent('2');
    expect(screen.getByTestId('first-alert-target')).toHaveTextContent('15000000');

    await act(async () => {
      fireEvent.click(screen.getByText('Remove alert'));
    });

    expect(mockedRemoveAlert).toHaveBeenCalledWith('client-token', 'product-1');
    expect(screen.getByTestId('alert-has-product-1')).toHaveTextContent('false');

    fireEvent.click(screen.getByText('Logout'));

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(screen.getByTestId('email')).toHaveTextContent('anonymous');
    expect(screen.getByTestId('alert-count')).toHaveTextContent('0');
  });
});
