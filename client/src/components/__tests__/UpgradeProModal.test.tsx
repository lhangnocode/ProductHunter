import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UpgradeProModal } from '../UpgradeProModal';

describe('UpgradeProModal', () => {
  it('renders the QR payment image and manual approval copy', () => {
    render(<UpgradeProModal isOpen onClose={() => {}} />);

    expect(screen.getByRole('img', { name: 'QR chuyển khoản nâng cấp Pro' })).toBeInTheDocument();
    expect(screen.getByText(/admin sẽ xác minh thủ công/i)).toBeInTheDocument();
  });
});
