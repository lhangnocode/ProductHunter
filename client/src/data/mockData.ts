export interface PlatformData {
  name: string;
  price: number;
  originalPrice: number;
  rating: number;
  reviews: number;
  shippingFee: number;
  url: string;
}

export interface PriceHistoryPoint {
  date: string;
  price: number;
}

export interface Product {
  id: string;
  name: string;
  image: string;
  category: string;
  platforms: PlatformData[];
  history: PriceHistoryPoint[];
  isTrending: boolean;
  fakeDiscountDetected: boolean;
}

export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'p1',
    name: 'Apple iPhone 15 Pro Max 256GB',
    image: 'https://picsum.photos/seed/iphone15/400/400',
    category: 'Electronics',
    platforms: [
      { name: 'Shopee', price: 29500000, originalPrice: 34990000, rating: 4.9, reviews: 1250, shippingFee: 15000, url: '#' },
      { name: 'Lazada', price: 29800000, originalPrice: 34990000, rating: 4.8, reviews: 890, shippingFee: 0, url: '#' },
      { name: 'Tiki', price: 29990000, originalPrice: 34990000, rating: 5.0, reviews: 450, shippingFee: 0, url: '#' },
    ],
    history: [
      { date: '2023-11', price: 34990000 },
      { date: '2023-12', price: 33500000 },
      { date: '2024-01', price: 32000000 },
      { date: '2024-02', price: 31500000 },
      { date: '2024-03', price: 29500000 },
    ],
    isTrending: true,
    fakeDiscountDetected: false,
  },
  {
    id: 'p2',
    name: 'Sony WH-1000XM5 Wireless Noise Canceling Headphones',
    image: 'https://picsum.photos/seed/sonywh/400/400',
    category: 'Audio',
    platforms: [
      { name: 'Shopee', price: 6500000, originalPrice: 8990000, rating: 4.7, reviews: 320, shippingFee: 20000, url: '#' },
      { name: 'Lazada', price: 6800000, originalPrice: 7500000, rating: 4.6, reviews: 210, shippingFee: 15000, url: '#' },
      { name: 'Tiki', price: 6990000, originalPrice: 8990000, rating: 4.9, reviews: 150, shippingFee: 0, url: '#' },
    ],
    history: [
      { date: '2023-11', price: 7500000 },
      { date: '2023-12', price: 7200000 },
      { date: '2024-01', price: 8990000 }, // Fake discount spike
      { date: '2024-02', price: 6800000 },
      { date: '2024-03', price: 6500000 },
    ],
    isTrending: true,
    fakeDiscountDetected: true,
  },
  {
    id: 'p3',
    name: 'Samsung Galaxy S24 Ultra 512GB',
    image: 'https://picsum.photos/seed/s24ultra/400/400',
    category: 'Electronics',
    platforms: [
      { name: 'Lazada', price: 31990000, originalPrice: 37490000, rating: 4.8, reviews: 560, shippingFee: 0, url: '#' },
      { name: 'Shopee', price: 32500000, originalPrice: 37490000, rating: 4.9, reviews: 420, shippingFee: 25000, url: '#' },
      { name: 'Tiki', price: 32990000, originalPrice: 37490000, rating: 4.7, reviews: 180, shippingFee: 0, url: '#' },
    ],
    history: [
      { date: '2024-01', price: 37490000 },
      { date: '2024-02', price: 35000000 },
      { date: '2024-03', price: 31990000 },
    ],
    isTrending: false,
    fakeDiscountDetected: false,
  },
  {
    id: 'p4',
    name: 'Logitech MX Master 3S Wireless Mouse',
    image: 'https://picsum.photos/seed/mxmaster/400/400',
    category: 'Accessories',
    platforms: [
      { name: 'Tiki', price: 2150000, originalPrice: 2490000, rating: 4.9, reviews: 890, shippingFee: 0, url: '#' },
      { name: 'Shopee', price: 2200000, originalPrice: 2490000, rating: 4.8, reviews: 1500, shippingFee: 15000, url: '#' },
      { name: 'Lazada', price: 2250000, originalPrice: 2490000, rating: 4.7, reviews: 600, shippingFee: 10000, url: '#' },
    ],
    history: [
      { date: '2023-11', price: 2300000 },
      { date: '2023-12', price: 2150000 },
      { date: '2024-01', price: 2490000 }, // Fake discount spike
      { date: '2024-02', price: 2200000 },
      { date: '2024-03', price: 2150000 },
    ],
    isTrending: true,
    fakeDiscountDetected: true,
  },
  {
    id: 'p5',
    name: 'Dyson V15 Detect Absolute Vacuum',
    image: 'https://picsum.photos/seed/dyson/400/400',
    category: 'Home Appliances',
    platforms: [
      { name: 'Shopee', price: 18500000, originalPrice: 21990000, rating: 4.9, reviews: 120, shippingFee: 50000, url: '#' },
      { name: 'Lazada', price: 18900000, originalPrice: 21990000, rating: 4.8, reviews: 85, shippingFee: 0, url: '#' },
    ],
    history: [
      { date: '2023-11', price: 21990000 },
      { date: '2023-12', price: 20500000 },
      { date: '2024-01', price: 19900000 },
      { date: '2024-02', price: 19000000 },
      { date: '2024-03', price: 18500000 },
    ],
    isTrending: false,
    fakeDiscountDetected: false,
  }
];
