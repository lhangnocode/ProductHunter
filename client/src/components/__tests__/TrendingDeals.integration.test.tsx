import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '../../utils/test-utils';
import { TrendingDeals } from '../TrendingDeals';
import { fetchTrendingDeals } from '../../services/trending_deal_api';

vi.mock('../../services/trending_deal_api', () => ({
  fetchTrendingDeals: vi.fn(),
}));

const mockedFetchTrendingDeals = vi.mocked(fetchTrendingDeals);

const deals = [
  {
    id: 'platform-product-1',
    product_id: 'product-1',
    product_name: 'iPhone 15 Pro Max 256GB',
    main_image_url: 'https://example.com/iphone.jpg',
    current_price: 24990000,
    original_price: 29990000,
    url: 'https://shop.example.com/iphone',
    deal_status: 'good',
    deal_label: 'Good deal',
    platform_name: 'Shopee',
    in_stock: true,
  },
  {
    id: 'platform-product-2',
    product_id: 'product-2',
    product_name: 'Samsung Galaxy S24 Ultra',
    main_image_url: 'https://example.com/samsung.jpg',
    current_price: 19990000,
    original_price: 25990000,
    url: 'https://shop.example.com/samsung',
    deal_status: 'extreme',
    deal_label: 'Extreme deal',
    platform_name: 'Tiki',
    in_stock: true,
  },
];

describe('TrendingDeals integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads trending deals from the API service and renders product cards', async () => {
    mockedFetchTrendingDeals.mockResolvedValueOnce(deals);

    render(
      <TrendingDeals
        onProductClick={vi.fn()}
        wishlistIds={new Set(['product-1'])}
        alertIds={new Set(['product-1'])}
        onToggleWishlist={vi.fn()}
      />,
    );

    expect(screen.getByText('Đang tìm kiếm deal cực hời...')).toBeInTheDocument();

    expect(await screen.findByText(/iPhone 15 Pro Max/i)).toBeInTheDocument();
    expect(screen.getByText(/Samsung Galaxy S24 Ultra/i)).toBeInTheDocument();
    expect(screen.getAllByTitle('Cập nhật cảnh báo giá')[0]).toBeInTheDocument();
    expect(mockedFetchTrendingDeals).toHaveBeenCalledTimes(1);
  });

  it('passes selected deal data through card click and wishlist toggle handlers', async () => {
    const onProductClick = vi.fn();
    const onToggleWishlist = vi.fn();
    mockedFetchTrendingDeals.mockResolvedValueOnce(deals);

    render(
      <TrendingDeals
        onProductClick={onProductClick}
        wishlistIds={new Set(['product-1'])}
        alertIds={new Set()}
        onToggleWishlist={onToggleWishlist}
      />,
    );

    const firstDealTitle = await screen.findByText(/iPhone 15 Pro Max/i);
    fireEvent.click(firstDealTitle);

    expect(onProductClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'platform-product-1', product_id: 'product-1' }),
      'platform-product-1',
    );

    fireEvent.click(screen.getAllByTitle('Thêm vào Wishlist')[0]);

    expect(onToggleWishlist).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'platform-product-1', product_id: 'product-1' }),
    );
  });

  it('renders the empty state when the service returns no deals', async () => {
    mockedFetchTrendingDeals.mockResolvedValueOnce([]);

    render(
      <TrendingDeals
        onProductClick={vi.fn()}
        wishlistIds={new Set()}
        alertIds={new Set()}
        onToggleWishlist={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Không có deal nào nổi bật lúc này.')).toBeInTheDocument();
    });
  });
});
