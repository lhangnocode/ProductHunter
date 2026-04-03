import React, { useState, useMemo } from 'react';
import { MOCK_PRODUCTS, Product } from './data/mockData';
import { ProductCard } from './components/ProductCard';
import { ProductDetail } from './components/ProductDetail';
import { LandingPage } from './components/LandingPage';
import { AuthModal } from './components/AuthModal';
import { ToastProvider, useToast } from './components/Toast';
import { UserProvider, useUser } from './context/UserContext';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { Search, TrendingUp, Heart, Bell, Menu, X, Command, Bird, Zap, User, ChevronRight, LogOut, LogIn, Sun, Moon, Languages, ChevronDown, Trash2, ExternalLink, CheckCircle2, Clock, ArrowRight, Smartphone, Home, Headphones, Watch } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

type Tab = 'search' | 'trending' | 'wishlist' | 'alerts';
type SortOption = 'trending' | 'price-asc' | 'price-desc' | 'rating';

function AppContent() {
  const [isAppStarted, setIsAppStarted] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>('All');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('trending');
  const [recentlyViewed, setRecentlyViewed] = useState<string[]>(() => {
    const saved = localStorage.getItem('recentlyViewed');
    return saved ? JSON.parse(saved) : [];
  });

  const { user, logout, wishlist, toggleWishlist, clearWishlist, alerts, removeAlert, setAlert, clearAlerts } = useUser();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const { showToast } = useToast();

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product);
    setRecentlyViewed(prev => {
      const filtered = prev.filter(id => id !== product.id);
      const next = [product.id, ...filtered].slice(0, 4);
      localStorage.setItem('recentlyViewed', JSON.stringify(next));
      return next;
    });
  };

  const recentlyViewedProducts = useMemo(() => 
    MOCK_PRODUCTS.filter(p => recentlyViewed.includes(p.id))
      .sort((a, b) => recentlyViewed.indexOf(a.id) - recentlyViewed.indexOf(b.id)),
    [recentlyViewed]
  );

  const categories = ['All', 'Electronics', 'Audio', 'Accessories', 'Home Appliances'];

  const searchResults = useMemo(() => {
    let results = [...MOCK_PRODUCTS];
    if (activeFilter !== 'All') {
      results = results.filter(p => p.category === activeFilter);
    }
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      results = results.filter(p => 
        p.name.toLowerCase().includes(query) || 
        p.category.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    results.sort((a, b) => {
      const aMinPrice = Math.min(...a.platforms.map(p => p.price));
      const bMinPrice = Math.min(...b.platforms.map(p => p.price));

      switch (sortBy) {
        case 'price-asc':
          return aMinPrice - bMinPrice;
        case 'price-desc':
          return bMinPrice - aMinPrice;
        case 'rating':
          return b.rating - a.rating;
        case 'trending':
        default:
          return (a.isTrending === b.isTrending) ? 0 : a.isTrending ? -1 : 1;
      }
    });

    return results;
  }, [searchQuery, activeFilter, sortBy]);

  const trendingProducts = useMemo(() => MOCK_PRODUCTS.filter(p => p.isTrending), []);
  const wishlistedProducts = useMemo(() => MOCK_PRODUCTS.filter(p => wishlist.includes(p.id)), [wishlist]);
  
  const handleAddWishlist = (product: Product) => {
    if (!user) {
      setIsAuthModalOpen(true);
      showToast(t('loginToSave'), 'info');
      return;
    }
    toggleWishlist(product.id);
    const isAdding = !wishlist.includes(product.id);
    showToast(isAdding ? t('addedToWishlist') : t('removedFromWishlist'));
  };

  const handleSetAlert = (product: Product, threshold: number) => {
    if (!user) {
      setIsAuthModalOpen(true);
      showToast(t('loginToSetAlert'), 'info');
      return;
    }
    setAlert(product.id, threshold);
    showToast(t('alertSetSuccess'));
  };

  if (!isAppStarted) {
    return <LandingPage onStart={() => setIsAppStarted(true)} />;
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 260,
        damping: 20
      }
    }
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
            <div className="mx-auto max-w-2xl text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.8, rotate: -5 }}
                animate={{ opacity: 1, scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 200, damping: 15 }}
                className="mb-6 inline-flex items-center gap-2 rounded-full bg-brand-primary/10 px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.2em] text-brand-primary ring-1 ring-inset ring-brand-primary/30 backdrop-blur-md"
              >
                <Zap size={12} className="animate-pulse" /> {t('realTimeComparison')}
              </motion.div>
              <h1 className="text-4xl font-black tracking-tighter text-slate-950 dark:text-white sm:text-6xl mb-6 leading-[0.9] font-display uppercase">
                {t('findDealsInAFlash').split('.')[0]} <br />
                <span className="text-brand-primary">{t('findDealsInAFlash').split('.')[1] || ''}</span>
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-base font-medium max-w-lg mx-auto leading-relaxed">
                {t('searchInstruction')}
              </p>
            </div>

            <div className="relative mx-auto max-w-xl group">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-6">
                <Search className="h-4 w-4 text-slate-400 transition-all duration-300 group-focus-within:text-brand-primary group-focus-within:scale-110" />
              </div>
              <input
                type="text"
                className="block w-full rounded-xl border-0 bg-white dark:bg-slate-900 py-5 pl-14 pr-16 text-lg font-bold text-slate-950 dark:text-white shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-none ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-primary hover:shadow-brand-primary/5 dark:hover:ring-brand-primary/50 outline-none font-sans"
                placeholder={t('searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="pointer-events-none absolute inset-y-0 right-6 flex items-center gap-2">
                <kbd className="hidden items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 text-[9px] font-bold text-slate-400 sm:flex shadow-sm">
                  <Command size={9} /> K
                </kbd>
              </div>
            </div>

            {!searchQuery && (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="mx-auto max-w-2xl space-y-10"
              >
                <div>
                  <h3 className="mb-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 text-center font-display">{t('popularSearches')}</h3>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    {['iPhone 15', 'Sony WH-1000XM5', 'MacBook Air M2', 'AirPods Pro', 'Samsung S24 Ultra'].map(tag => (
                      <motion.button
                        key={tag}
                        variants={itemVariants}
                        whileHover={{ scale: 1.03, y: -1 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setSearchQuery(tag)}
                        className="rounded-full bg-white dark:bg-slate-900 px-4 py-2 text-xs font-bold text-slate-600 dark:text-slate-400 shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-brand-primary hover:ring-brand-primary/30 uppercase tracking-wide"
                      >
                        {tag}
                      </motion.button>
                    ))}
                  </div>
                </div>

                <div className="pt-6">
                  <h3 className="mb-6 text-[9px] font-black uppercase tracking-[0.3em] text-slate-400 text-center font-display">{t('featuredCategories')}</h3>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    <motion.button 
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setActiveFilter('Electronics')}
                      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-4 shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:shadow-lg hover:ring-brand-primary/30 text-left"
                    >
                      <div className="relative z-10">
                        <span className="text-[8px] font-black uppercase tracking-[0.15em] text-brand-primary font-display">{t('hotNow')}</span>
                        <h3 className="mt-1 text-sm font-black tracking-tight text-slate-900 dark:text-white font-display uppercase">{t('techDeals')}</h3>
                        <p className="mt-0.5 text-[9px] font-bold text-slate-400">{MOCK_PRODUCTS.filter(p => p.category === 'Electronics').length} {t('products')}</p>
                      </div>
                      <div className="mt-3 flex items-center gap-1 text-[9px] font-black text-brand-primary uppercase tracking-wider">
                        {t('exploreNow')} <ArrowRight size={10} />
                      </div>
                      <Smartphone size={60} className="absolute -bottom-3 -right-3 rotate-12 opacity-[0.03] dark:opacity-[0.05] transition-transform group-hover:scale-110 group-hover:opacity-10" />
                    </motion.button>

                    <motion.button 
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setActiveFilter('Audio')}
                      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-4 shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:shadow-lg hover:ring-brand-primary/30 text-left"
                    >
                      <div className="relative z-10">
                        <span className="text-[8px] font-black uppercase tracking-[0.15em] text-brand-primary font-display">{t('trending')}</span>
                        <h3 className="mt-1 text-sm font-black tracking-tight text-slate-900 dark:text-white font-display uppercase">{t('audioDeals')}</h3>
                        <p className="mt-0.5 text-[9px] font-bold text-slate-400">{MOCK_PRODUCTS.filter(p => p.category === 'Audio').length} {t('products')}</p>
                      </div>
                      <div className="mt-3 flex items-center gap-1 text-[9px] font-black text-brand-primary uppercase tracking-wider">
                        {t('exploreNow')} <ArrowRight size={10} />
                      </div>
                      <Headphones size={60} className="absolute -bottom-3 -right-3 rotate-12 opacity-[0.03] dark:opacity-[0.05] transition-transform group-hover:scale-110 group-hover:opacity-10" />
                    </motion.button>

                    <motion.button 
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setActiveFilter('Accessories')}
                      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-4 shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:shadow-lg hover:ring-brand-primary/30 text-left"
                    >
                      <div className="relative z-10">
                        <span className="text-[8px] font-black uppercase tracking-[0.15em] text-brand-primary font-display">Essential</span>
                        <h3 className="mt-1 text-sm font-black tracking-tight text-slate-900 dark:text-white font-display uppercase">{t('essentialAccessories')}</h3>
                        <p className="mt-0.5 text-[9px] font-bold text-slate-400">{MOCK_PRODUCTS.filter(p => p.category === 'Accessories').length} {t('products')}</p>
                      </div>
                      <div className="mt-3 flex items-center gap-1 text-[9px] font-black text-brand-primary uppercase tracking-wider">
                        {t('exploreNow')} <ArrowRight size={10} />
                      </div>
                      <Watch size={60} className="absolute -bottom-3 -right-3 rotate-12 opacity-[0.03] dark:opacity-[0.05] transition-transform group-hover:scale-110 group-hover:opacity-10" />
                    </motion.button>

                    <motion.button 
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setActiveFilter('Home Appliances')}
                      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-4 shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:shadow-lg hover:ring-brand-primary/30 text-left"
                    >
                      <div className="relative z-10">
                        <span className="text-[8px] font-black uppercase tracking-[0.15em] text-brand-primary font-display">Home</span>
                        <h3 className="mt-1 text-sm font-black tracking-tight text-slate-900 dark:text-white font-display uppercase">{t('homeDeals')}</h3>
                        <p className="mt-0.5 text-[9px] font-bold text-slate-400">{MOCK_PRODUCTS.filter(p => p.category === 'Home Appliances').length} {t('products')}</p>
                      </div>
                      <div className="mt-3 flex items-center gap-1 text-[9px] font-black text-brand-primary uppercase tracking-wider">
                        {t('exploreNow')} <ArrowRight size={10} />
                      </div>
                      <Home size={60} className="absolute -bottom-3 -right-3 rotate-12 opacity-[0.03] dark:opacity-[0.05] transition-transform group-hover:scale-110 group-hover:opacity-10" />
                    </motion.button>
                  </div>
                </div>

                {/* Recently Viewed Section - Editorial Style */}
                {recentlyViewedProducts.length > 0 && (
                  <motion.div
                    variants={itemVariants}
                    className="pt-12 border-t border-slate-200 dark:border-slate-800"
                  >
                    <div className="mb-6 flex items-end justify-between">
                      <div>
                        <span className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-primary mb-1 block font-display">{t('yourHistory')}</span>
                        <h3 className="text-2xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">
                          {t('recentlyViewed')}
                        </h3>
                      </div>
                      <div className="flex gap-1.5">
                        <div className="h-1 w-6 rounded-full bg-brand-primary" />
                        <div className="h-1 w-1.5 rounded-full bg-slate-200 dark:bg-slate-800" />
                        <div className="h-1 w-1.5 rounded-full bg-slate-200 dark:bg-slate-800" />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                      {recentlyViewedProducts.map((product, idx) => (
                        <motion.div
                          key={product.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                        >
                          <ProductCard 
                            product={product}
                            onClick={handleProductClick}
                            isWishlisted={wishlist.includes(product.id)}
                            onToggleWishlist={(e) => {
                              e.stopPropagation();
                              handleAddWishlist(product);
                            }}
                          />
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {searchQuery && (
              <div className="space-y-8">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-6">
                  <div>
                    <span className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-primary mb-1 block font-display">{t('explore')}</span>
                    <h2 className="text-2xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">
                      {t('resultsFor')} <span className="text-brand-primary">"{searchQuery}"</span>
                    </h2>
                    <p className="mt-0.5 text-[11px] font-bold text-slate-400">{searchResults.length} {t('products')} {t('found')}</p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="relative group">
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as SortOption)}
                        className="appearance-none rounded-xl bg-white dark:bg-slate-900 px-5 py-2.5 pr-10 text-[11px] font-black text-slate-700 dark:text-slate-300 ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all hover:bg-slate-50 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-primary shadow-sm uppercase tracking-wider"
                      >
                        <option value="trending">{t('trending')}</option>
                        <option value="price-asc">{t('priceLowToHigh')}</option>
                        <option value="price-desc">{t('priceHighToLow')}</option>
                        <option value="rating">{t('rating')}</option>
                      </select>
                      <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400 group-hover:text-brand-primary transition-colors" />
                    </div>

                    <button 
                      onClick={() => setSearchQuery('')}
                      className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-500 transition-all border border-transparent hover:border-rose-200"
                      title={t('clearSearch')}
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>

                <motion.div 
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                  className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                >
                  {searchResults.map((product) => (
                    <motion.div key={product.id} variants={itemVariants}>
                      <ProductCard 
                        product={product} 
                        onClick={handleProductClick} 
                        isWishlisted={wishlist.includes(product.id)}
                        onToggleWishlist={(e) => {
                          e.stopPropagation();
                          handleAddWishlist(product);
                        }}
                      />
                    </motion.div>
                  ))}
                </motion.div>
                
                {searchResults.length === 0 && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center justify-center rounded-[2.5rem] border border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 py-24 text-center backdrop-blur-sm"
                  >
                    <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-100 dark:bg-slate-800 text-slate-400 shadow-xl">
                      <Search size={40} />
                    </div>
                    <h3 className="text-xl font-black text-slate-900 dark:text-white font-display uppercase tracking-tight">{t('noResults')}</h3>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 font-medium max-w-xs">
                      {t('noResultsSubtitle')}
                    </p>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        );
      case 'trending':
        return (
          <div className="space-y-10">
            <div className="flex items-center gap-6 border-b border-slate-200 dark:border-slate-800 pb-8">
              <motion.div 
                initial={{ rotate: -10, scale: 0.8 }}
                animate={{ rotate: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 200 }}
                className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-primary/10 text-brand-primary ring-1 ring-inset ring-brand-primary/20 shadow-xl shadow-brand-primary/10 backdrop-blur-md"
              >
                <TrendingUp size={32} strokeWidth={2.5} />
              </motion.div>
              <div>
                <span className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-primary mb-1 block font-display">Market Trends</span>
                <h2 className="text-3xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">{t('trendingDeals')}</h2>
                <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{t('trendingSubtitle')}</p>
              </div>
            </div>
            <motion.div 
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            >
              {trendingProducts.map((product) => (
                <motion.div key={product.id} variants={itemVariants}>
                  <ProductCard 
                    product={product} 
                    onClick={handleProductClick} 
                    isWishlisted={wishlist.includes(product.id)}
                    onToggleWishlist={(e) => {
                      e.stopPropagation();
                      handleAddWishlist(product);
                    }}
                  />
                </motion.div>
              ))}
            </motion.div>
          </div>
        );
      case 'wishlist':
        return (
          <div className="space-y-10">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-8">
              <div className="flex items-center gap-6">
                <motion.div 
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  whileHover={{ scale: 1.1 }}
                  className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 dark:bg-rose-950/30 text-rose-500 ring-1 ring-inset ring-rose-100 dark:ring-rose-900/30 shadow-xl shadow-rose-500/10 backdrop-blur-md"
                >
                  <Heart size={32} className="fill-rose-500" />
                </motion.div>
                <div>
                  <span className="text-[9px] font-black uppercase tracking-[0.3em] text-rose-500 mb-1 block font-display">Saved Items</span>
                  <h2 className="text-3xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">{t('wishlist')}</h2>
                  <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{t('wishlistSubtitle')}</p>
                </div>
              </div>
              
              {wishlistedProducts.length > 0 && (
                <button
                  onClick={() => {
                    if (window.confirm(t('confirmClearWishlist'))) {
                      clearWishlist();
                      showToast(t('removedFromWishlist'));
                    }
                  }}
                  className="flex items-center gap-2.5 rounded-xl bg-white dark:bg-slate-900 px-6 py-3 text-xs font-black text-slate-600 dark:text-slate-400 transition-all hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-500 ring-1 ring-inset ring-slate-200 dark:ring-slate-800 hover:ring-rose-200 dark:hover:ring-rose-800 shadow-sm uppercase tracking-wider"
                >
                  <Trash2 size={16} />
                  {t('clearAll')}
                </button>
              )}
            </div>

            {wishlistedProducts.length > 0 ? (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
              >
                {wishlistedProducts.map((product) => (
                  <motion.div key={product.id} variants={itemVariants}>
                    <ProductCard 
                      product={product} 
                      onClick={handleProductClick}
                      onRemove={() => handleAddWishlist(product)}
                    />
                  </motion.div>
                ))}
              </motion.div>
            ) : (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center rounded-[2.5rem] border-2 border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 py-24 text-center backdrop-blur-sm"
              >
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-rose-50 dark:bg-rose-950/30 text-rose-400 shadow-xl shadow-rose-500/5">
                  <Heart size={40} />
                </div>
                <h3 className="text-xl font-black text-slate-900 dark:text-white font-display uppercase tracking-tight">{t('emptyWishlist')}</h3>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 font-medium max-w-xs mb-8">
                  {t('emptyWishlistSubtitle')}
                </p>
                <button
                  onClick={() => setActiveTab('search')}
                  className="flex items-center gap-2.5 rounded-xl bg-brand-primary px-8 py-3.5 text-xs font-black text-white shadow-xl shadow-brand-primary/20 transition-all hover:scale-105 active:scale-95 uppercase tracking-wider"
                >
                  {t('exploreNow')}
                </button>
              </motion.div>
            )}
          </div>
        );
      case 'alerts':
        return (
          <div className="space-y-10">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-8">
              <div className="flex items-center gap-6">
                <motion.div 
                  initial={{ rotate: -15 }}
                  animate={{ rotate: 0 }}
                  whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                  className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-accent/10 text-brand-accent ring-1 ring-inset ring-brand-accent/20 shadow-xl shadow-brand-accent/10 backdrop-blur-md"
                >
                  <Bell size={32} className="fill-brand-accent" strokeWidth={2.5} />
                </motion.div>
                <div>
                  <span className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-accent mb-1 block font-display">Active Alerts</span>
                  <h2 className="text-3xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">{t('priceAlerts')}</h2>
                  <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{t('alertsSubtitle')}</p>
                </div>
              </div>

              {alerts.length > 0 && (
                <button
                  onClick={() => {
                    if (window.confirm(t('confirmClearAlerts'))) {
                      clearAlerts();
                      showToast(t('alertSetSuccess'));
                    }
                  }}
                  className="flex items-center gap-2.5 rounded-xl bg-white dark:bg-slate-900 px-6 py-3 text-xs font-black text-slate-600 dark:text-slate-400 transition-all hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-500 ring-1 ring-inset ring-slate-200 dark:ring-slate-800 hover:ring-rose-200 dark:hover:ring-rose-800 shadow-sm uppercase tracking-wider"
                >
                  <Trash2 size={16} />
                  {t('clearAll')}
                </button>
              )}
            </div>

            {alerts.length > 0 ? (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 gap-6 lg:grid-cols-2"
              >
                {alerts.map((alert) => {
                  const product = MOCK_PRODUCTS.find(p => p.id === alert.productId);
                  if (!product) return null;
                  const currentMinPrice = Math.min(...product.platforms.map(p => p.price));
                  const isReached = currentMinPrice <= alert.threshold;

                  return (
                    <motion.div
                      key={alert.productId}
                      variants={itemVariants}
                      whileHover={{ scale: 1.01, y: -2 }}
                      className="group relative flex flex-col sm:flex-row items-center gap-6 rounded-3xl bg-white dark:bg-slate-900 p-6 shadow-lg border border-slate-200/50 dark:border-slate-800/50 transition-all hover:shadow-xl hover:border-brand-primary/30"
                    >
                      <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800">
                        <img src={product.image} alt={product.name} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
                      </div>

                      <div className="flex-grow space-y-3 text-center sm:text-left">
                        <div>
                          <h3 className="text-lg font-black text-slate-900 dark:text-white line-clamp-1 font-display tracking-tight uppercase">{product.name}</h3>
                          <div className="mt-1.5 flex flex-wrap items-center justify-center sm:justify-start gap-2">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[8px] font-black uppercase tracking-widest ${
                              isReached ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/30 shadow-sm' : 'bg-amber-100 text-amber-600 dark:bg-amber-950/30 shadow-sm'
                            }`}>
                              {isReached ? <CheckCircle2 size={10} /> : <Clock size={10} />}
                              {isReached ? t('targetReached') : t('waiting')}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-center sm:justify-start gap-6">
                          <div>
                            <p className="text-[8px] font-black uppercase tracking-[0.15em] text-slate-400 mb-0.5">{t('currentPrice')}</p>
                            <p className="text-xl font-black text-slate-900 dark:text-white font-mono tracking-tighter">
                              {new Intl.NumberFormat(language === 'vi' ? 'vi-VN' : 'en-US', { style: 'currency', currency: language === 'vi' ? 'VND' : 'USD' }).format(currentMinPrice)}
                            </p>
                          </div>
                          <div className="h-8 w-px bg-slate-100 dark:bg-slate-800" />
                          <div>
                            <p className="text-[8px] font-black uppercase tracking-[0.15em] text-slate-400 mb-0.5">{t('targetPrice')}</p>
                            <p className="text-xl font-black text-brand-primary font-mono tracking-tighter">
                              {new Intl.NumberFormat(language === 'vi' ? 'vi-VN' : 'en-US', { style: 'currency', currency: language === 'vi' ? 'VND' : 'USD' }).format(alert.threshold)}
                            </p>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800 shadow-inner">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(100, (alert.threshold / currentMinPrice) * 100)}%` }}
                            className={`h-full rounded-full transition-all shadow-sm ${isReached ? 'bg-brand-success' : 'bg-brand-primary'}`}
                          />
                        </div>
                      </div>

                      <div className="flex flex-row sm:flex-col gap-2 w-full sm:w-auto">
                        <button
                          onClick={() => handleProductClick(product)}
                          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-slate-50 dark:bg-slate-800 px-4 py-2.5 text-xs font-black text-slate-600 dark:text-slate-400 transition-all hover:bg-brand-primary/10 hover:text-brand-primary border border-transparent hover:border-brand-primary/20 uppercase tracking-wider"
                        >
                          <ExternalLink size={16} />
                          <span className="hidden lg:inline">{t('viewProduct')}</span>
                        </button>
                        <button
                          onClick={() => removeAlert(alert.productId)}
                          className="flex items-center justify-center rounded-xl bg-rose-50 dark:bg-rose-950/30 p-2.5 text-rose-500 transition-all hover:bg-rose-500 hover:text-white shadow-sm border border-transparent hover:border-rose-200"
                          title={t('delete')}
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            ) : (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center rounded-[2.5rem] border-2 border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 py-24 text-center backdrop-blur-sm"
              >
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-100 dark:bg-slate-800 text-slate-400 shadow-xl">
                  <Bell size={40} />
                </div>
                <h3 className="text-xl font-black text-slate-900 dark:text-white font-display uppercase tracking-tight">{t('noAlerts')}</h3>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 font-medium max-w-xs mb-8">
                  {t('noAlertsSubtitle')}
                </p>
                <button
                  onClick={() => setActiveTab('search')}
                  className="flex items-center gap-2.5 rounded-xl bg-brand-primary px-8 py-3.5 text-xs font-black text-white shadow-xl shadow-brand-primary/20 transition-all hover:scale-105 active:scale-95 uppercase tracking-wider"
                >
                  {t('exploreNow')}
                </button>
              </motion.div>
            )}
          </div>
        );
    }
  };

  const NavItem = ({ icon: Icon, label, tab }: { icon: any, label: string, tab: Tab }) => (
    <motion.button
      whileHover={{ x: 3, backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }}
      whileTap={{ scale: 0.98 }}
      onClick={() => {
        setActiveTab(tab);
        setSelectedProduct(null);
        setIsMobileMenuOpen(false);
      }}
      className={`relative group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[9px] font-black transition-all font-display uppercase tracking-[0.2em]
        ${activeTab === tab && !selectedProduct 
          ? 'text-white' 
          : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
        }
      `}
    >
      <Icon size={14} className="relative z-10" strokeWidth={activeTab === tab && !selectedProduct ? 3 : 2} />
      <span className="relative z-10">{label}</span>
      
      {tab === 'wishlist' && wishlist.length > 0 && (
        <span className={`relative z-10 ml-auto rounded-md px-1.5 py-0.5 text-[8px] font-black ${activeTab === tab && !selectedProduct ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
          {wishlist.length}
        </span>
      )}
      {tab === 'alerts' && alerts.length > 0 && (
        <span className={`relative z-10 ml-auto rounded-md px-1.5 py-0.5 text-[8px] font-black ${activeTab === tab && !selectedProduct ? 'bg-white/20 text-white' : 'bg-brand-accent/10 text-brand-accent'}`}>
          {alerts.length}
        </span>
      )}

      {activeTab === tab && !selectedProduct && (
        <motion.div
          layoutId="activeTabIndicator"
          className="absolute inset-0 rounded-lg bg-brand-primary shadow-lg shadow-brand-primary/20"
          transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
        />
      )}
    </motion.button>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-brand-primary/10 selection:text-brand-primary transition-colors duration-300">
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
      
      {/* Background Decorative Elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] rounded-full bg-brand-primary/10 blur-[150px] animate-pulse" />
        <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] rounded-full bg-brand-accent/10 blur-[130px]" />
        <div className="absolute -bottom-[10%] left-[20%] w-[45%] h-[45%] rounded-full bg-emerald-500/10 blur-[140px] animate-pulse" />
      </div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-slate-200/40 dark:border-slate-800/40 bg-white/70 dark:bg-slate-950/70 backdrop-blur-xl">
          <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-2.5">
          <div className="flex items-center gap-8">
            <button 
              onClick={() => {
                setIsAppStarted(false);
                setActiveTab('search');
                setSelectedProduct(null);
              }}
              className="flex items-center gap-2 text-base font-black tracking-tighter text-slate-950 dark:text-white transition-transform active:scale-95 group"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-primary text-white shadow-lg shadow-brand-primary/20 group-hover:rotate-12 transition-transform">
                <Bird size={16} strokeWidth={3} />
              </div>
              <span className="hidden sm:inline font-display uppercase">PriceHawk<span className="text-brand-primary">.</span></span>
            </button>

            {/* Desktop Search in Navbar */}
            {(activeTab !== 'search' || selectedProduct) && (
              <div className="hidden md:block relative w-64 group">
                <Search className="absolute left-3 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-primary transition-colors" />
                <input
                  type="text"
                  placeholder={t('searchProducts')}
                  className="w-full rounded-lg border-0 bg-slate-100 dark:bg-slate-900 py-1.5 pl-8 pr-4 text-[10px] font-black uppercase tracking-wider text-slate-950 dark:text-white ring-1 ring-inset ring-transparent transition-all focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-brand-primary font-display"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (activeTab !== 'search') setActiveTab('search');
                    if (selectedProduct) setSelectedProduct(null);
                  }}
                />
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:flex items-center gap-1 rounded-lg bg-slate-100/50 dark:bg-slate-800/50 p-0.5">
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ rotate: 180, scale: 0.9 }}
                onClick={toggleTheme}
                className="rounded-md p-1.5 text-slate-500 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white transition-all"
                title={theme === 'light' ? 'Dark Mode' : 'Light Mode'}
              >
                {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setLanguage(language === 'vi' ? 'en' : 'vi')}
                className="flex items-center gap-1 rounded-md p-1.5 text-slate-500 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white transition-all font-black text-[8px] font-display"
                title="Change Language"
              >
                <Languages size={12} />
                <span className="uppercase tracking-widest">{language}</span>
              </motion.button>
            </div>

            <div className="hidden sm:flex items-center gap-1 rounded-lg bg-slate-100/50 dark:bg-slate-800/50 p-0.5">
              <motion.button 
                whileHover={{ scale: 1.05, y: -1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveTab('wishlist')}
                className={`relative rounded-md p-1.5 transition-all ${activeTab === 'wishlist' ? 'bg-white dark:bg-slate-700 text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
              >
                <Heart size={16} />
                {wishlist.length > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-brand-primary text-[8px] font-black text-white ring-2 ring-white dark:ring-slate-950 font-display">
                    {wishlist.length}
                  </span>
                )}
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05, y: -1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveTab('alerts')}
                className={`relative rounded-md p-1.5 transition-all ${activeTab === 'alerts' ? 'bg-white dark:bg-slate-700 text-brand-accent shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
              >
                <Bell size={16} />
                {alerts.length > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-brand-accent text-[8px] font-black text-white ring-2 ring-white dark:ring-slate-950 font-display">
                    {alerts.length}
                  </span>
                )}
              </motion.button>
            </div>

            <div className="h-5 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block" />

            {user ? (
              <div className="flex items-center gap-2.5">
                <div className="hidden text-right lg:block">
                  <p className="text-[10px] font-black text-slate-900 dark:text-white font-display uppercase tracking-wider leading-none">{user.name}</p>
                  <p className="text-[8px] font-bold text-slate-500 dark:text-slate-400 leading-none mt-1">{user.email}</p>
                </div>
                <motion.button 
                  whileHover={{ scale: 1.05, rotate: 5 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    logout();
                    showToast(t('logoutSuccess'));
                  }}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-primary/10 text-brand-primary font-black transition-transform ring-1 ring-brand-primary/20 text-[10px] font-display uppercase"
                  title={t('logout')}
                >
                  {user.name[0]}
                </motion.button>
              </div>
            ) : (
              <motion.button 
                whileHover={{ scale: 1.05, backgroundColor: '#000' }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-2 rounded-lg bg-brand-secondary px-3.5 py-1.5 text-[9px] font-black text-white shadow-lg shadow-brand-secondary/20 transition-all uppercase tracking-[0.2em] font-display"
              >
                <LogIn size={14} />
                <span className="hidden sm:inline">{t('login')}</span>
              </motion.button>
            )}

            <button 
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
              className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
            >
              {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px] relative z-10">
        {/* Sidebar */}
        <aside className={`
          fixed left-0 top-[52px] z-40 flex h-[calc(100vh-52px)] w-56 flex-col border-r border-slate-200/40 dark:border-slate-800/40 glass-surface transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:sticky lg:translate-x-0'}
        `}>
          <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-6">
            <div className="mb-2.5 px-3 text-[8px] font-black uppercase tracking-[0.3em] text-slate-400/80 font-display">{t('explore')}</div>
            <NavItem icon={Search} label={t('searchAndCompare')} tab="search" />
            <NavItem icon={TrendingUp} label={t('trendingDeals')} tab="trending" />
            
            <div className="mb-2.5 mt-8 px-3 text-[8px] font-black uppercase tracking-[0.3em] text-slate-400/80 font-display">{t('personal')}</div>
            <NavItem icon={Heart} label={t('wishlist')} tab="wishlist" />
            <NavItem icon={Bell} label={t('priceAlerts')} tab="alerts" />

            <div className="mt-auto pt-8 pb-4">
              <div className="rounded-xl bg-gradient-to-br from-brand-primary/10 to-brand-accent/10 p-4 ring-1 ring-inset ring-brand-primary/10">
                <p className="text-[10px] font-black text-brand-primary mb-1 font-display uppercase tracking-wider">{t('sidebarPromoTitle')}</p>
                <p className="text-[8px] font-bold text-slate-500 dark:text-slate-400 leading-relaxed mb-3">
                  {t('sidebarPromoDesc')}
                </p>
                <button className="w-full rounded-lg bg-brand-primary py-2 text-[8px] font-black text-white shadow-lg shadow-brand-primary/20 transition-all hover:scale-105 active:scale-95 uppercase tracking-widest font-display">
                  {t('upgradeNow')}
                </button>
              </div>
            </div>
          </nav>
        </aside>

        {/* Overlay for mobile */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 z-20 bg-slate-900/20 backdrop-blur-sm lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0 px-4 py-8 sm:px-8 lg:px-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedProduct ? 'detail' : activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="mx-auto max-w-6xl"
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <ThemeProvider>
        <UserProvider>
          <ToastProvider>
            <AppContent />
          </ToastProvider>
        </UserProvider>
      </ThemeProvider>
    </LanguageProvider>
  );
}

