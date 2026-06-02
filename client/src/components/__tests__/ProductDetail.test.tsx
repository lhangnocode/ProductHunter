import { describe, expect, it } from 'vitest';
import { getPlatformName } from '../ProductDetail';

describe('ProductDetail platform metadata', () => {
  it('renders active crawler CSV platform IDs', () => {
    expect(getPlatformName(7)).toBe('FPT Shop');
    expect(getPlatformName(8)).toBe('Phong Vũ');
    expect(getPlatformName(9)).toBe('CellphoneS');
  });

  it('does not treat old CellphoneS IDs as canonical platform IDs', () => {
    expect(getPlatformName(4)).toBe('Sàn khác');
    expect(getPlatformName(5)).toBe('Sàn khác');
    expect(getPlatformName(6)).toBe('Sàn khác');
  });

  it('infers CellphoneS from seller URLs when platform ID is unknown', () => {
    expect(getPlatformName(999, { url: 'https://cellphones.com.vn/iphone-15' })).toBe('CellphoneS');
    expect(getPlatformName(null, { affiliate_url: 'https://cellphones.com.vn/iphone-15?aff=1' })).toBe('CellphoneS');
  });

  it('falls back to Sàn khác for unknown platform IDs', () => {
    expect(getPlatformName(999)).toBe('Sàn khác');
  });
});
