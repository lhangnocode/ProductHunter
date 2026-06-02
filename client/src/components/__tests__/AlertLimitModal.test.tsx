import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AlertLimitModal } from '../AlertLimitModal';

describe('AlertLimitModal', () => {
  it('shows usage and opens upgrade flow', () => {
    const onClose = vi.fn();
    const onUpgrade = vi.fn();

    render(<AlertLimitModal isOpen used={5} onClose={onClose} onUpgrade={onUpgrade} />);

    expect(screen.getByText('Đã đạt giới hạn cảnh báo')).toBeInTheDocument();
    expect(screen.getAllByText(/5\/5/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByText('Nâng cấp Pro'));

    expect(onUpgrade).toHaveBeenCalledOnce();
  });
});
