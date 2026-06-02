import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UpgradeProModal } from '../UpgradeProModal';
import { UserProvider } from '../../context/UserContext';
import { ToastProvider } from '../Toast';  // ✅ Thêm import này

describe('UpgradeProModal', () => {
  it('renders the QR payment image and manual approval copy', () => {
    render(
      <ToastProvider>                    {/* ✅ Bọc thêm ToastProvider */}
        <UserProvider>
          <UpgradeProModal isOpen onClose={() => {}} />
        </UserProvider>
      </ToastProvider>
    );

    // Lưu ý: alt text thực tế là "QR Code" chứ không phải "QR chuyển khoản nâng cấp Pro"
    expect(screen.getByRole('img', { name: 'QR Code' })).toBeInTheDocument();
    expect(screen.getByText(/admin sẽ xác minh thủ công/i)).toBeInTheDocument();
  });
});