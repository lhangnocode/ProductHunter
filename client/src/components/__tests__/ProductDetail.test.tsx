import { describe, expect, it } from 'vitest';
import { getPlatformName } from '../ProductDetail';

describe('ProductDetail platform metadata', () => {
  it('renders CellphoneS for platform ID 5', () => {
    expect(getPlatformName(5)).toBe('CellphoneS');
  });

  it('falls back to Sàn khác for unknown platform IDs', () => {
    expect(getPlatformName(999)).toBe('Sàn khác');
  });
});
