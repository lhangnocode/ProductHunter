import React, { createContext, useContext, useState, useEffect } from 'react';

type Language = 'vi' | 'en';

interface Translations {
  [key: string]: {
    [key in Language]: string;
  };
}

const translations: Translations = {
  searchProducts: { vi: 'Tìm kiếm sản phẩm', en: 'Search Products' },
  searchPlaceholder: { vi: 'Ví dụ: iPhone 15 Pro Max 256GB...', en: 'Example: iPhone 15 Pro Max 256GB...' },
  trendingDeals: { vi: 'Trending Deals', en: 'Trending Deals' },
  trendingSubtitle: { vi: 'Sản phẩm đang giảm giá thật sự (đã kiểm tra lịch sử giá)', en: 'Products with real discounts (price history verified)' },
  wishlist: { vi: 'Wishlist', en: 'Wishlist' },
  wishlistSubtitle: { vi: 'Theo dõi giá các sản phẩm yêu thích tự động', en: 'Track prices of your favorite products automatically' },
  priceAlerts: { vi: 'Price Alerts', en: 'Price Alerts' },
  alertsSubtitle: { vi: 'Quản lý các cảnh báo giá bạn đã đặt', en: 'Manage your price alerts' },
  login: { vi: 'Đăng nhập', en: 'Login' },
  logout: { vi: 'Đăng xuất', en: 'Logout' },
  register: { vi: 'Đăng ký', en: 'Register' },
  all: { vi: 'Tất cả', en: 'All' },
  electronics: { vi: 'Điện tử', en: 'Electronics' },
  audio: { vi: 'Âm thanh', en: 'Audio' },
  accessories: { vi: 'Phụ kiện', en: 'Accessories' },
  homeAppliances: { vi: 'Gia dụng', en: 'Home Appliances' },
  sortBy: { vi: 'Sắp xếp theo', en: 'Sort by' },
  priceLowToHigh: { vi: 'Giá: Thấp đến Cao', en: 'Price: Low to High' },
  priceHighToLow: { vi: 'Giá: Cao đến Thấp', en: 'Price: High to Low' },
  newest: { vi: 'Mới nhất', en: 'Newest' },
  trending: { vi: 'Thịnh hành', en: 'Trending' },
  resultsFor: { vi: 'Kết quả cho', en: 'Results for' },
  noResults: { vi: 'Không tìm thấy sản phẩm', en: 'No products found' },
  tryOtherKeywords: { vi: 'Thử sử dụng từ khóa khác hoặc dán trực tiếp link sản phẩm từ Shopee, Lazada, Tiki.', en: 'Try other keywords or paste a link from Shopee, Lazada, Tiki.' },
  popularSearches: { vi: 'Tìm kiếm phổ biến', en: 'Popular Searches' },
  featuredCategories: { vi: 'Danh mục nổi bật', en: 'Featured Categories' },
  products: { vi: 'sản phẩm', en: 'products' },
  clearSearch: { vi: 'Xóa tìm kiếm', en: 'Clear search' },
  extensionTitle: { vi: 'ProductHunter Extension', en: 'ProductHunter Extension' },
  extensionSubtitle: { vi: 'Tự động so sánh giá khi lướt Shopee/Lazada.', en: 'Automatically compare prices while browsing Shopee/Lazada.' },
  installNow: { vi: 'Cài đặt ngay', en: 'Install Now' },
  mainMenu: { vi: 'Menu chính', en: 'Main Menu' },
  personal: { vi: 'Cá nhân', en: 'Personal' },
  support: { vi: 'Hỗ trợ', en: 'Support' },
  usageGuide: { vi: 'Hướng dẫn sử dụng', en: 'Usage Guide' },
  explore: { vi: 'Khám phá', en: 'Explore' },
  searchAndCompare: { vi: 'Tìm kiếm & So sánh', en: 'Search & Compare' },
  realTimeComparison: { vi: 'So sánh giá thời gian thực', en: 'Real-time price comparison' },
  findDealsInAFlash: { vi: 'Tìm deal hời trong chớp mắt.', en: 'Find great deals in a flash.' },
  searchInstruction: { vi: 'Dán link sản phẩm từ Shopee, Lazada, Tiki hoặc nhập tên sản phẩm để so sánh giá và xem lịch sử biến động.', en: 'Paste a link from Shopee, Lazada, Tiki or enter a product name to compare prices and view history.' },
  priceDesired: { vi: 'Mức giá mong muốn', en: 'Desired Price' },
  action: { vi: 'Hành động', en: 'Action' },
  delete: { vi: 'Xóa', en: 'Delete' },
  emptyWishlist: { vi: 'Danh sách trống', en: 'Wishlist is empty' },
  emptyWishlistSubtitle: { vi: 'Bạn chưa lưu sản phẩm nào. Hãy bấm vào biểu tượng trái tim trên sản phẩm để lưu lại.', en: 'You haven\'t saved any products. Click the heart icon on a product to save it.' },
  noAlerts: { vi: 'Chưa có cảnh báo giá nào', en: 'No price alerts yet' },
  noAlertsSubtitle: { vi: 'Đặt báo giá trong chi tiết sản phẩm để nhận thông báo khi giá giảm đến mức bạn mong muốn.', en: 'Set a price alert in product details to get notified when the price drops to your target.' },
  welcomeBack: { vi: 'Chào mừng trở lại!', en: 'Welcome back!' },
  joinProductHunter: { vi: 'Tham gia cùng ProductHunter', en: 'Join ProductHunter' },
  loginToSeeWishlist: { vi: 'Đăng nhập để xem danh sách theo dõi của bạn.', en: 'Login to see your tracking list.' },
  createAccountForAlerts: { vi: 'Tạo tài khoản để nhận thông báo giá tự động.', en: 'Create an account for automatic price alerts.' },
  fullName: { vi: 'Họ và tên', en: 'Full Name' },
  yourEmail: { vi: 'Email của bạn', en: 'Your Email' },
  password: { vi: 'Mật khẩu', en: 'Password' },
  orContinueWith: { vi: 'Hoặc tiếp tục với', en: 'Or continue with' },
  noAccountRegister: { vi: 'Chưa có tài khoản? Đăng ký ngay', en: 'No account? Register now' },
  haveAccountLogin: { vi: 'Đã có tài khoản? Đăng nhập', en: 'Already have an account? Login' },
  loginSuccess: { vi: 'Đăng nhập thành công!', en: 'Login successful!' },
  registerSuccess: { vi: 'Đăng ký thành công!', en: 'Registration successful!' },
  logoutSuccess: { vi: 'Đã đăng xuất', en: 'Logged out' },
  user: { vi: 'Người dùng', en: 'User' },
  fillAllInfo: { vi: 'Vui lòng điền đầy đủ thông tin', en: 'Please fill in all information' },
  loginToSave: { vi: 'Vui lòng đăng nhập để lưu sản phẩm', en: 'Please login to save products' },
  loginToSetAlert: { vi: 'Vui lòng đăng nhập để đặt báo giá', en: 'Please login to set price alert' },
  addedToWishlist: { vi: 'Đã thêm vào Wishlist', en: 'Added to Wishlist' },
  removedFromWishlist: { vi: 'Đã xóa khỏi Wishlist', en: 'Removed from Wishlist' },
  alertSetSuccess: { vi: 'Đã đặt cảnh báo giá thành công', en: 'Price alert set successfully' },
  back: { vi: 'Quay lại', en: 'Back' },
  comparePrices: { vi: 'So sánh giá', en: 'Compare Prices' },
  priceHistory: { vi: 'Lịch sử giá', en: 'Price History' },
  lowestPrice6Months: { vi: 'Giá thấp nhất 6 tháng', en: 'Lowest price in 6 months' },
  highestPrice6Months: { vi: 'Giá cao nhất 6 tháng', en: 'Highest price in 6 months' },
  setAlert: { vi: 'Đặt cảnh báo', en: 'Set Alert' },
  buyNow: { vi: 'Mua ngay', en: 'Buy Now' },
  seller: { vi: 'Người bán', en: 'Seller' },
  rating: { vi: 'Đánh giá', en: 'Rating' },
  reviews: { vi: 'nhận xét', en: 'reviews' },
  stock: { vi: 'Kho hàng', en: 'Stock' },
  inStock: { vi: 'Còn hàng', en: 'In Stock' },
  outOfStock: { vi: 'Hết hàng', en: 'Out of Stock' },
  lastUpdated: { vi: 'Cập nhật lần cuối', en: 'Last updated' },
  bestPriceAt: { vi: 'Giá tốt nhất tại', en: 'Best price at' },
  shouldBuy: { vi: 'Nên mua', en: 'Recommended' },
  fakeDiscountWarning: { vi: 'Cảnh báo tăng giá ảo', en: 'Fake discount warning' },
  cautionBuy: { vi: 'Cẩn trọng khi mua', en: 'Caution when buying' },
  cautionBuyDesc: { vi: 'Sản phẩm có dấu hiệu tăng giá trước khi giảm. Không nên mua lúc này.', en: 'Product shows signs of price hiking before discounting. Not recommended now.' },
  goldenTimeBuy: { vi: 'Thời điểm vàng để mua', en: 'Golden time to buy' },
  goldenTimeBuyDesc: { vi: 'Giá đang ở mức thấp nhất trong 6 tháng qua. Chốt đơn ngay!', en: 'Price is at its lowest in 6 months. Buy now!' },
  stablePrice: { vi: 'Giá đang ổn định', en: 'Price is stable' },
  stablePriceDesc: { vi: 'Mức giá hiện tại tương đương với trung bình các tháng trước.', en: 'Current price is similar to previous months\' average.' },
  notifyPriceDrop: { vi: 'Nhận thông báo khi giá giảm', en: 'Get notified when price drops' },
  enterPrice: { vi: 'Nhập mức giá...', en: 'Enter price...' },
  setPriceAlert: { vi: 'Đặt báo giá', en: 'Set alert' },
  priceAlertSet: { vi: 'Đã đặt', en: 'Set' },
  comparePlatforms: { vi: 'So sánh giá các sàn', en: 'Compare platforms' },
  cheapest: { vi: 'Rẻ nhất', en: 'Cheapest' },
  shipping: { vi: 'Ship', en: 'Ship' },
  freeShipping: { vi: 'Freeship', en: 'Freeship' },
  goToSeller: { vi: 'Tới nơi bán', en: 'Go to seller' },
  priceHistory6Months: { vi: 'Lịch sử giá (6 tháng)', en: 'Price history (6 months)' },
  trendingDown: { vi: 'Đang có xu hướng giảm', en: 'Trending down' },
  clearAll: { vi: 'Xóa tất cả', en: 'Clear all' },
  exploreNow: { vi: 'Khám phá ngay', en: 'Explore now' },
  hotNow: { vi: 'Đang Hot', en: 'Hot Now' },
  techDeals: { vi: 'Deal Công Nghệ', en: 'Tech Deals' },
  audioDeals: { vi: 'Deal Âm Thanh', en: 'Audio Deals' },
  essentialAccessories: { vi: 'Phụ Kiện Thiết Yếu', en: 'Essential Accessories' },
  homeDeals: { vi: 'Deal Gia Dụng', en: 'Home Deals' },
  yourHistory: { vi: 'Lịch sử của bạn', en: 'Your History' },
  currentPrice: { vi: 'Giá hiện tại', en: 'Current price' },
  targetPrice: { vi: 'Giá mục tiêu', en: 'Target price' },
  viewProduct: { vi: 'Xem sản phẩm', en: 'View product' },
  status: { vi: 'Trạng thái', en: 'Status' },
  waiting: { vi: 'Đang chờ giá giảm', en: 'Waiting for drop' },
  targetReached: { vi: 'Đã đạt mục tiêu!', en: 'Target reached!' },
  confirmClearWishlist: { vi: 'Xóa toàn bộ wishlist?', en: 'Clear entire wishlist?' },
  confirmClearAlerts: { vi: 'Xóa toàn bộ cảnh báo?', en: 'Clear all alerts?' },
  dealAnalysis: { vi: 'Phân tích Deal', en: 'Deal Analysis' },
  lowestEver: { vi: 'Giá thấp nhất lịch sử', en: 'Lowest ever price' },
  priceIsDropping: { vi: 'Giá đang giảm mạnh!', en: 'Price is dropping fast!' },
  buyNowStimulus: { vi: 'Đây là thời điểm tốt nhất để mua sản phẩm này.', en: 'This is the best time to buy this product.' },
  waitStimulus: { vi: 'Bạn nên đợi thêm hoặc đặt báo giá để có giá tốt hơn.', en: 'You should wait or set an alert for a better price.' },
  recentlyViewed: { vi: 'Sản phẩm vừa xem', en: 'Recently Viewed' },
  viewAll: { vi: 'Xem tất cả', en: 'View All' },
  features: { vi: 'Tính năng', en: 'Features' },
  platforms: { vi: 'Nền tảng', en: 'Platforms' },
  community: { vi: 'Cộng đồng', en: 'Community' },
  pricing: { vi: 'Bảng giá', en: 'Pricing' },
  startNow: { vi: 'Bắt đầu ngay', en: 'Start Now' },
  huntDealsAI: { vi: 'Săn deal hời nhất cùng AI', en: 'Hunt best deals with AI' },
  smartShopping: { vi: 'Mua sắm thông minh', en: 'Smart Shopping' },
  maxSavings: { vi: 'Tiết kiệm tối đa', en: 'Maximum Savings' },
  heroDesc: { vi: 'ProductHunter tự động theo dõi giá, phân tích lịch sử và cảnh báo khi có deal hời từ Shopee, Lazada, Tiki và hơn thế nữa.', en: 'ProductHunter automatically tracks prices, analyzes history and alerts you when there are great deals from Shopee, Lazada, Tiki and more.' },
  startHunting: { vi: 'Bắt đầu săn deal', en: 'Start Hunting Deals' },
  howItWorks: { vi: 'Xem cách hoạt động', en: 'How it works' },
  priceDroppedDeep: { vi: 'Giá giảm sâu!', en: 'Price dropped deep!' },
  mockupDesc: { vi: 'Giá vừa giảm 2.500.000₫ trên Shopee Mall. Mua ngay kẻo lỡ!', en: 'Price just dropped 2,500,000₫ on Shopee Mall. Buy now!' },
  everythingYouNeed: { vi: 'Mọi thứ bạn cần để mua sắm rẻ hơn', en: 'Everything you need to shop cheaper' },
  aiTechDesc: { vi: 'Công nghệ AI tiên tiến giúp bạn không bao giờ phải mua hớ bất kỳ sản phẩm nào.', en: 'Advanced AI technology helps you never overpay for any product.' },
  priceHistory6MonthsDesc: { vi: 'Xem biểu đồ biến động giá chi tiết để biết giá hiện tại có thực sự là deal hời hay không.', en: 'View detailed price fluctuation charts to know if the current price is really a good deal.' },
  priceAlertsDesc: { vi: 'Đặt mức giá mong muốn và chúng tôi sẽ báo ngay khi giá chạm mốc.', en: 'Set your desired price and we will notify you as soon as the price hits the mark.' },
  newNotification: { vi: 'Thông báo mới', en: 'New Notification' },
  priceDroppedTo: { vi: 'Giá đã giảm xuống', en: 'Price dropped to' },
  dealAnalysisDesc: { vi: 'AI tự động đánh giá độ "ngon" của deal dựa trên dữ liệu lịch sử.', en: 'AI automatically evaluates the "quality" of the deal based on historical data.' },
  excellentDealScore: { vi: 'Điểm Deal cực tốt', en: 'Excellent Deal Score' },
  multiPlatformComparisonDesc: { vi: 'Tự động tìm kiếm và so sánh giá từ tất cả các sàn TMĐT lớn nhất Việt Nam.', en: 'Automatically search and compare prices from all the largest e-commerce platforms in Vietnam.' },
  readyToSave: { vi: 'Sẵn sàng để tiết kiệm?', en: 'Ready to save?' },
  joinUsersDesc: { vi: 'Gia nhập cùng hơn 50,000 người dùng đang săn deal mỗi ngày với ProductHunter.', en: 'Join over 50,000 users hunting deals every day with ProductHunter.' },
  startFreeNow: { vi: 'Bắt đầu miễn phí ngay', en: 'Start for free now' },
  footerDesc: { vi: 'Trợ lý mua sắm thông minh hàng đầu Việt Nam. Giúp bạn luôn mua được hàng với giá tốt nhất.', en: 'Vietnam\'s leading smart shopping assistant. Helping you always buy at the best price.' },
  product: { vi: 'Sản phẩm', en: 'Product' },
  company: { vi: 'Công ty', en: 'Company' },
  aboutUs: { vi: 'Về chúng tôi', en: 'About Us' },
  blog: { vi: 'Blog', en: 'Blog' },
  terms: { vi: 'Điều khoản', en: 'Terms' },
  privacy: { vi: 'Bảo mật', en: 'Privacy' },
  chromeExtension: { vi: 'Tiện ích Chrome', en: 'Chrome Extension' },
  mobileApp: { vi: 'Ứng dụng di động', en: 'Mobile App' },
  sidebarPromoTitle: { vi: 'ProductHunter Pro', en: 'ProductHunter Pro' },
  sidebarPromoDesc: { vi: 'Mở khóa tính năng theo dõi giá không giới hạn và thông báo tức thì.', en: 'Unlock unlimited price tracking and instant notifications.' },
  upgradeNow: { vi: 'Nâng cấp ngay', en: 'Upgrade Now' },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('language');
    if (saved === 'vi' || saved === 'en') return saved;
    return 'vi';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  const t = (key: string) => {
    return translations[key]?.[language] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
