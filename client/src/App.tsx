import React, { useState, useMemo } from 'react';
import { MOCK_PRODUCTS, Product } from './data/mockData';
import { ProductCard } from './components/ProductCard';
import { ProductDetail } from './components/ProductDetail';
import { Search, TrendingUp, Heart, Bell, Menu, X, ShoppingBag, Command } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

type Tab = 'search' | 'trending' | 'wishlist' | 'alerts';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<{ productId: string; threshold: number }[]>([]);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return MOCK_PRODUCTS;
    const query = searchQuery.toLowerCase();
    return MOCK_PRODUCTS.filter(p => 
      p.name.toLowerCase().includes(query) || 
      p.category.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  const trendingProducts = useMemo(() => MOCK_PRODUCTS.filter(p => p.isTrending), []);
  const wishlistedProducts = useMemo(() => MOCK_PRODUCTS.filter(p => wishlist.includes(p.id)), [wishlist]);
  
  const handleAddWishlist = (product: Product) => {
    setWishlist(prev => 
      prev.includes(product.id) 
        ? prev.filter(id => id !== product.id) 
        : [...prev, product.id]
    );
  };

  const handleSetAlert = (product: Product, threshold: number) => {
    setAlerts(prev => {
      const existing = prev.findIndex(a => a.productId === product.id);
      if (existing >= 0) {
        const newAlerts = [...prev];
        newAlerts[existing] = { productId: product.id, threshold };
        return newAlerts;
      }
      return [...prev, { productId: product.id, threshold }];
    });
  };

  const renderContent = () => {
    if (selectedProduct) {
      return (
        <ProductDetail 
          product={selectedProduct} 
          onBack={() => setSelectedProduct(null)}
          onAddWishlist={handleAddWishlist}
          onSetAlert={handleSetAlert}
          isWishlisted={wishlist.includes(selectedProduct.id)}
        />
      );
    }

    switch (activeTab) {
      case 'search':
        return (
          <div className="space-y-8">
            <div className="relative mx-auto max-w-3xl">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-5">
                <Search className="h-5 w-5 text-zinc-400" />
              </div>
              <input
                type="text"
                className="block w-full rounded-full border-0 bg-white py-4 pl-14 pr-32 text-lg text-zinc-900 shadow-sm ring-1 ring-inset ring-zinc-200/50 transition-all placeholder:text-zinc-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                placeholder="Tìm kiếm sản phẩm, dán link Shopee/Lazada..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="pointer-events-none absolute inset-y-0 right-4 flex items-center gap-2">
                <kbd className="hidden items-center gap-1 rounded border border-zinc-200 bg-zinc-50 px-2 py-1 text-[10px] font-medium text-zinc-500 sm:flex">
                  <Command size={12} /> K
                </kbd>
              </div>
            </div>

            {searchQuery && (
              <h2 className="text-xl font-bold tracking-tight text-zinc-900">Kết quả tìm kiếm cho "{searchQuery}"</h2>
            )}

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {searchResults.map(product => (
                <ProductCard 
                  key={product.id} 
                  product={product} 
                  onClick={setSelectedProduct} 
                />
              ))}
              {searchResults.length === 0 && (
                <div className="col-span-full py-20 text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-zinc-100">
                    <Search className="h-8 w-8 text-zinc-400" />
                  </div>
                  <h3 className="text-lg font-medium text-zinc-900">Không tìm thấy sản phẩm</h3>
                  <p className="mt-1 text-zinc-500">Thử tìm kiếm với từ khóa khác hoặc dán trực tiếp link sản phẩm.</p>
                </div>
              )}
            </div>
          </div>
        );
      case 'trending':
        return (
          <div className="space-y-8">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 text-rose-600">
                <TrendingUp size={24} />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-zinc-900">Trending Deals</h2>
                <p className="text-sm text-zinc-500">Sản phẩm đang giảm giá thật sự (đã kiểm tra lịch sử giá)</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {trendingProducts.map(product => (
                <ProductCard 
                  key={product.id} 
                  product={product} 
                  onClick={setSelectedProduct} 
                />
              ))}
            </div>
          </div>
        );
      case 'wishlist':
        return (
          <div className="space-y-8">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-pink-100 text-pink-600">
                <Heart size={24} />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-zinc-900">Wishlist</h2>
                <p className="text-sm text-zinc-500">Theo dõi giá các sản phẩm yêu thích tự động</p>
              </div>
            </div>
            {wishlistedProducts.length > 0 ? (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {wishlistedProducts.map(product => (
                  <ProductCard 
                    key={product.id} 
                    product={product} 
                    onClick={setSelectedProduct} 
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-zinc-200 bg-white py-32 text-center">
                <Heart size={48} className="mb-4 text-zinc-300" />
                <h3 className="mb-2 text-lg font-medium text-zinc-900">Chưa có sản phẩm nào</h3>
                <p className="text-sm text-zinc-500">Hãy thêm sản phẩm vào wishlist để theo dõi giá dễ dàng hơn.</p>
              </div>
            )}
          </div>
        );
      case 'alerts':
        return (
          <div className="space-y-8">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-amber-600">
                <Bell size={24} />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-zinc-900">Price Alerts</h2>
                <p className="text-sm text-zinc-500">Quản lý các cảnh báo giá bạn đã đặt</p>
              </div>
            </div>
            {alerts.length > 0 ? (
              <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-zinc-200/50">
                <table className="w-full text-left text-sm">
                  <thead className="bg-zinc-50/50">
                    <tr>
                      <th className="px-6 py-4 font-medium text-zinc-500">Sản phẩm</th>
                      <th className="px-6 py-4 font-medium text-zinc-500">Mức giá mong muốn</th>
                      <th className="px-6 py-4 text-right font-medium text-zinc-500">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {alerts.map(alert => {
                      const product = MOCK_PRODUCTS.find(p => p.id === alert.productId);
                      if (!product) return null;
                      return (
                        <tr key={alert.productId} className="transition-colors hover:bg-zinc-50/50">
                          <td className="px-6 py-4">
                            <div className="flex cursor-pointer items-center gap-4" onClick={() => setSelectedProduct(product)}>
                              <img src={product.image} alt={product.name} className="h-12 w-12 rounded-xl border border-zinc-100 object-cover" />
                              <span className="font-medium text-zinc-900">{product.name}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 font-mono font-bold text-indigo-600">
                            {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(alert.threshold)}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button 
                              onClick={() => setAlerts(prev => prev.filter(a => a.productId !== alert.productId))}
                              className="rounded-lg px-3 py-1.5 font-medium text-rose-500 transition-colors hover:bg-rose-50 hover:text-rose-600"
                            >
                              Xóa
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-zinc-200 bg-white py-32 text-center">
                <Bell size={48} className="mb-4 text-zinc-300" />
                <h3 className="mb-2 text-lg font-medium text-zinc-900">Chưa có cảnh báo giá nào</h3>
                <p className="text-sm text-zinc-500">Đặt báo giá trong chi tiết sản phẩm để nhận thông báo khi giá giảm.</p>
              </div>
            )}
          </div>
        );
    }
  };

  const NavItem = ({ icon: Icon, label, tab }: { icon: any, label: string, tab: Tab }) => (
    <button
      onClick={() => {
        setActiveTab(tab);
        setSelectedProduct(null);
        setIsMobileMenuOpen(false);
      }}
      className={`group flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-left text-sm font-medium transition-all
        ${activeTab === tab && !selectedProduct 
          ? 'bg-zinc-900 text-white shadow-sm' 
          : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
        }
      `}
    >
      <Icon size={18} className={activeTab === tab && !selectedProduct ? 'text-zinc-300' : 'text-zinc-400 group-hover:text-zinc-600'} />
      {label}
      {tab === 'wishlist' && wishlist.length > 0 && (
        <span className={`ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ${activeTab === tab && !selectedProduct ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-100 text-zinc-500'}`}>
          {wishlist.length}
        </span>
      )}
      {tab === 'alerts' && alerts.length > 0 && (
        <span className={`ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ${activeTab === tab && !selectedProduct ? 'bg-zinc-800 text-zinc-300' : 'bg-indigo-100 text-indigo-600'}`}>
          {alerts.length}
        </span>
      )}
    </button>
  );

  return (
    <div className="min-h-screen bg-zinc-50 font-sans text-zinc-900 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Mobile Header */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-zinc-200/80 bg-white/80 px-4 py-3 backdrop-blur-xl lg:hidden">
        <div className="flex items-center gap-2 text-lg font-bold tracking-tight text-zinc-900">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white">
            <ShoppingBag size={16} strokeWidth={2.5} />
          </div>
          PriceTracker
        </div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="rounded-lg p-2 text-zinc-600 hover:bg-zinc-100">
          {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <div className="mx-auto flex max-w-[1600px]">
        {/* Sidebar */}
        <aside className={`
          fixed left-0 top-0 z-20 flex h-screen w-72 flex-col border-r border-zinc-200/80 bg-zinc-50/50 transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0 bg-white' : '-translate-x-full lg:sticky lg:translate-x-0'}
        `}>
          <div className="hidden items-center gap-2 p-6 lg:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white shadow-sm">
              <ShoppingBag size={16} strokeWidth={2.5} />
            </div>
            <span className="text-xl font-bold tracking-tight text-zinc-900">PriceTracker<span className="text-indigo-600">.</span></span>
          </div>
          
          <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
            <div className="mb-3 px-4 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Menu chính</div>
            <NavItem icon={Search} label="Tìm kiếm & So sánh" tab="search" />
            <NavItem icon={TrendingUp} label="Trending Deals" tab="trending" />
            
            <div className="mb-3 mt-8 px-4 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Cá nhân</div>
            <NavItem icon={Heart} label="Wishlist" tab="wishlist" />
            <NavItem icon={Bell} label="Price Alerts" tab="alerts" />
          </nav>

          <div className="p-4">
            <div className="rounded-2xl bg-indigo-50/50 p-4 ring-1 ring-inset ring-indigo-500/10">
              <h4 className="mb-1 text-sm font-bold text-indigo-900">Extension Browser</h4>
              <p className="mb-4 text-xs leading-relaxed text-indigo-700/80">Tự động so sánh giá khi lướt Shopee/Lazada.</p>
              <button className="w-full rounded-xl bg-white py-2 text-xs font-bold text-indigo-600 shadow-sm ring-1 ring-inset ring-zinc-200 transition-all hover:bg-zinc-50 active:scale-95">
                Cài đặt ngay
              </button>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 z-10 bg-zinc-900/20 backdrop-blur-sm lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-x-hidden p-4 sm:p-6 lg:p-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedProduct ? 'detail' : activeTab}
              initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -10, filter: 'blur(4px)' }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="mx-auto max-w-5xl"
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

