import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UpgradeProModal } from '../UpgradeProModal';
import { UserProvider } from '../../context/UserContext';
import { ToastProvider } from '../Toast';
import * as authService from '../../services/auth';
import * as wishlistService from '../../services/wishlist';
import * as priceAlertService from '../../services/priceAlert';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock services
vi.mock('../../services/auth', () => ({
  authService: {
    getMe: vi.fn(),
  },
}));

vi.mock('../../services/wishlist', () => ({
  wishlistService: {
    getWishlist: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../../services/priceAlert', () => ({
  priceAlertService: {
    getAlerts: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../../services/payment', () => ({
  paymentService: {
    createPaymentRequest: vi.fn().mockResolvedValue({}),
  },
}));

describe('UpgradeProModal', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // Mock getMe to return a user
    vi.mocked(authService.authService.getMe).mockResolvedValue({
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      plan: 0,
    });
  });

  it('renders the QR payment image and payment button', async () => {
    render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Check for the QR code image
    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'QR Code' })).toBeInTheDocument();
    });

    // Check for PRO title
    expect(screen.getByText(/Gói PRO/i)).toBeInTheDocument();

    // Check for QR payment instruction text
    expect(screen.getByText(/Quét mã QR để thanh toán/i)).toBeInTheDocument();

    // Check for payment button
    expect(screen.getByRole('button', { name: /Tôi đã thanh toán/i })).toBeInTheDocument();
  });

  it('renders all PRO features', async () => {
    render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Check for PRO features
    await waitFor(() => {
      expect(screen.getByText(/Không giới hạn Alert/i)).toBeInTheDocument();
      expect(screen.getByText(/Ưu tiên săn deal hot/i)).toBeInTheDocument();
      expect(screen.getByText(/Không quảng cáo/i)).toBeInTheDocument();
      expect(screen.getByText(/Hỗ trợ 24\/7/i)).toBeInTheDocument();
    });
  });

  it('renders payment account information', async () => {
    render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Check for account info section title
    expect(screen.getByText(/Thông tin tài khoản/i)).toBeInTheDocument();

    // Check for account details
    await waitFor(() => {
      expect(screen.getByText('DANG DINH KHANG')).toBeInTheDocument();
      expect(screen.getByText('8870380066')).toBeInTheDocument();
      expect(screen.getByText(/Ngân hàng BIDV/i)).toBeInTheDocument();
      expect(screen.getByText(/59[.,]000\s?đ/i)).toBeInTheDocument();
    });
  });

  it('renders file upload section', async () => {
    render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Check for upload label
    await waitFor(() => {
      expect(screen.getByText(/Tải lên biên lai \(Ảnh\)/i)).toBeInTheDocument();
    });

    // Check for file input text
    expect(screen.getByText(/Nhấn để chọn ảnh/i)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const handleClose = vi.fn();
    render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen onClose={handleClose} />
        </UserProvider>
      </ToastProvider>
    );

    // Find and click the close button (X icon button)
    const closeButton = screen.getAllByRole('button').find(
      btn => !btn.textContent?.includes('Tôi đã thanh toán')
    );
    
    await waitFor(() => {
      fireEvent.click(closeButton!);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <ToastProvider>
        <UserProvider>
          <UpgradeProModal isOpen={false} onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Check that modal content doesn't exist
    expect(container.querySelector('.fixed.inset-0.z-\\[40\\]')).not.toBeInTheDocument();
  });
});
