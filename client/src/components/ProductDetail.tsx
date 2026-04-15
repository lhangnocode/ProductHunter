import React, { useEffect, useState } from 'react';
import { formatDisplayName } from '../lib/utils';
import { createPortal } from 'react-dom';
import { PriceChart } from './PriceChart';
import { ArrowLeft, Star, Bell, Heart, AlertTriangle, CheckCircle2, TrendingDown, Info, ShoppingBag, Package, ShoppingCart, ExternalLink, Zap, Share2, ShieldCheck, X, Loader2, ChevronDown, Trash2 } from 'lucide-react'; // Thêm X và Loader2
import { motion } from 'motion/react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useUser } from '../context/UserContext'; // Thêm useUser
import { useToast } from './Toast'; // Thêm useToast
import { fetchPriceHistory, PriceAnalysis, fetchPriceAnalysis, fetchPlatformProductsByProductId, PlatformProduct } from '../services/price_record_api';

interface ProductDetailProps {
  product: any; 
  platformProduct: any;
  initialPlatformId: string;
  onBack: () => void;
  onAddWishlist: (p: any) => void;
  onSetAlert: (product: any, threshold: number) => void;
  isWishlisted: boolean;
}

export function ProductDetail({ product,platformProduct, initialPlatformId, onBack, onAddWishlist, onSetAlert, isWishlisted }: ProductDetailProps) {
  const { t, language } = useLanguage();
  const { user, setAlert, alertIds, removeAlert } = useUser(); // Lấy thông tin user, setAlert, alertIds và removeAlert
  const { showToast } = useToast(); // Lấy hàm hiển thị thông báo

  // State quản lý các sàn
  const [allPlatformProducts, setAllPlatformProducts] = useState<PlatformProduct[]>([]);
  const [selectedPlatformProduct, setSelectedPlatformProduct] = useState<PlatformProduct | null>(null);
  const [platformsLoading, setPlatformsLoading] = useState(true);

  const [historyData, setHistoryData] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<PriceAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  // State cho Modal Cảnh báo giá
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [targetPriceInput, setTargetPriceInput] = useState('');
  const [isSubmittingAlert, setIsSubmittingAlert] = useState(false);
  
  // State để show/hide platform selector
  const [showPlatformSelector, setShowPlatformSelector] = useState(false);

  // Guard: chỉ gọi API khi ID là UUID hợp lệ (tránh crash với ID mock như p1, p2)
  const isValidUUID = (id: string) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);

  const currentPlatformData = selectedPlatformProduct || platformProduct;
  const currentPrice = parseFloat(String(currentPlatformData?.current_price)) || 0;
  const originalPrice = parseFloat(String(currentPlatformData?.original_price)) || 0;
  const currentPlatformId = selectedPlatformProduct?.id || initialPlatformId;
  const targetProductId = platformProduct.product_id ?? platformProduct.id;
  const isAlerted = alertIds.has(targetProductId);

  // Lọc bỏ URL ảnh mock/placeholder không hợp lệ
  const isRealImageUrl = (url: string | null | undefined): boolean => {
    if (!url || typeof url !== 'string' || url.trim() === '') return false;
    const mockPatterns = ['picsum.photos', 'placeholder.com', 'placehold.co', 'loremflickr', 'dummyimage', 'via.placeholder'];
    return !mockPatterns.some(p => url.includes(p));
  };
 

  const normalizeImageUrl = (url: string | null | undefined): string | null => {
    if (!url || typeof url !== 'string' || url.trim() === '') return null;
    let cleaned = url.trim();
    if (cleaned.includes(',')) {
      cleaned = cleaned.split(',')[0].trim();
    }
    cleaned = cleaned.split(/\s+/)[0].trim();
    if (cleaned.startsWith('//')) {
      cleaned = `https:${cleaned}`;
    } else if (cleaned.startsWith('cdn2.fptshop.com.vn') || cleaned.startsWith('fptshop.com.vn')) {
      cleaned = `https://${cleaned}`;
    }
    return cleaned || null;
  };

  // Ảnh và tên luôn lấy từ prop gốc, loại bỏ URL mock
  const rawImage = product?.main_image_url || currentPlatformData?.main_image_url;
  const normalizedImage = normalizeImageUrl(rawImage);
  const productImage = isRealImageUrl(normalizedImage) ? normalizedImage : null;
  const rawName = product?.product_name || product?.normalized_name || currentPlatformData?.raw_name || currentPlatformData?.raw_name || '';
  const productName = formatDisplayName(rawName);
  
  // State track lỗi ảnh
  const [imgError, setImgError] = React.useState(false);

  // Reset imgError khi product thay đổi
  React.useEffect(() => { setImgError(false); }, [productImage]);

  // Check if we have valid price data (only PlatformProduct has current_price)
  const hasPriceData = currentPlatformData?.current_price !== undefined && currentPlatformData?.current_price !== null;

  // 1. Fetch all platform products for this product
  // Note: platformProduct can be either a Product (from search) or PlatformProduct
  // When it's a Product: platformProduct.id = product_id
  // When it's a PlatformProduct: platformProduct.product_id = product_id

  useEffect(() => {
    async function loadPlatformProducts() {
      setPlatformsLoading(true);
      try {
        const productId = platformProduct?.product_id || platformProduct?.id;
        if (!productId || !isValidUUID(String(productId))) {
          console.warn('ID không hợp lệ, bỏ qua API:', productId);
          return;
        }
        const platforms = await fetchPlatformProductsByProductId(productId);
        setAllPlatformProducts(platforms);
        if (platforms.length > 0) {
          const matching = platforms.find(p => p.id === initialPlatformId);
          setSelectedPlatformProduct(matching || platforms[0]);
        }
      } catch (err) {
        console.error('Lỗi khi fetch platform products:', err);
      } finally {
        setPlatformsLoading(false);
      }
    }
    loadPlatformProducts();
  }, [platformProduct?.product_id || platformProduct?.id, initialPlatformId]);

  // HÀM XỬ LÝ LƯU CẢNH BÁO GIÁ
  const handleSaveAlert = async () => {
    if (!user) {
      showToast('Vui lòng đăng nhập để sử dụng tính năng này!', 'error');
      return;
    }

    const numericPrice = parseFloat(targetPriceInput.replace(/\D/g, ''));
    if (isNaN(numericPrice) || numericPrice <= 0) {
      showToast('Vui lòng nhập mức giá hợp lệ!', 'error');
      return;
    }

    setIsSubmittingAlert(true);
    try {
      const targetProductId = platformProduct.product_id ?? platformProduct.id;
      
      await setAlert(targetProductId, numericPrice);

      showToast('Đã đặt cảnh báo giá thành công!', 'success');
      setIsAlertModalOpen(false);
      setTargetPriceInput('');
    } catch (error: any) {
      showToast(error.message || 'Lỗi khi đặt cảnh báo giá', 'error');
    } finally {
      setIsSubmittingAlert(false);
    }
  };

  // Hàm format tiền tệ khi user đang gõ
  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, ''); 
    if (value) {
      setTargetPriceInput(new Intl.NumberFormat('vi-VN').format(Number(value)));
    } else {
      setTargetPriceInput('');
    }
  };

  useEffect(() => {
    async function loadHistoryAndAnalysis() {
      if (!currentPlatformId || !isValidUUID(String(currentPlatformId))) return;
      setLoading(true);
      try {
        const [historyRes, analysisRes] = await Promise.all([
          fetchPriceHistory(currentPlatformId),
          fetchPriceAnalysis(currentPlatformId, currentPrice, originalPrice)
        ]);
        const formattedHistory = historyRes.map(record => ({
          date: new Date(record.recorded_at).toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US', {
            month: 'short',
            day: 'numeric'
          }),
          price: Number(record.price)
        }));
        setHistoryData(formattedHistory);
        setAnalysis(analysisRes);
      } catch (err) {
        console.error('Lỗi lấy lịch sử giá:', err);
      } finally {
        setLoading(false);
      }
    }
    loadHistoryAndAnalysis();
  }, [currentPlatformId, language, currentPrice, originalPrice]);

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'extreme': return 'text-rose-600 bg-rose-50 border-rose-100 dark:bg-rose-950/30 dark:text-rose-400';
      case 'fake': return 'text-amber-600 bg-amber-50 border-amber-100 dark:bg-amber-950/30 dark:text-amber-400';
      case 'good': return 'text-emerald-600 bg-emerald-50 border-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-400';
      default: return 'text-slate-600 bg-slate-50 border-slate-100 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  const formatPrice = (value: number) => {
    const locale = language === 'vi' ? 'vi-VN' : 'en-US';
    const currency = language === 'vi' ? 'VND' : 'USD';
    const convertedValue = language === 'en' ? value / 25000 : value;
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: language === 'en' ? 2 : 0
    }).format(convertedValue);
  };

  const getPlatformName = (id: number) => {
    switch (id) {
      case 1: return 'Shopee';
      case 2: return 'Tiki';
      case 5: return 'CellPhones';
      case 7: return 'FPT Shop';
      case 8: return 'Phong Vũ';
      default: return 'Sàn khác';
    }
  };

  const platformName = getPlatformName(currentPlatformData.platform_id);

  const handleSelectPlatform = (platform: PlatformProduct) => {
    setSelectedPlatformProduct(platform);
    setShowPlatformSelector(false);
  };

  

  return (
    <>
      <div className="overflow-hidden rounded-[2.5rem] bg-white dark:bg-slate-900 shadow-2xl border border-slate-200/60 dark:border-slate-800/60">

        {/* 1. Header Buttons */}
        <div className="sticky top-0 z-30 flex items-center justify-between border-b p-4 backdrop-blur-xl bg-white/80 dark:bg-slate-900/80">
          <button onClick={onBack} className="flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase border rounded-full transition-colors hover:bg-slate-100 dark:hover:bg-slate-800">
            <ArrowLeft size={14} /> {t('back')}
          </button>
          
          {/* NÚT ALERT CHUÔNG - THAY ĐỔI MÀU DỰA TRÊN STATE */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => {
                if (!user) {
                  showToast('Vui lòng đăng nhập để đặt cảnh báo giá!', 'info');
                  return;
                }
                setIsAlertModalOpen(true);
              }}
              className={`h-9 w-9 flex items-center justify-center rounded-full border transition-colors ${
                isAlerted
                  ? 'bg-brand-accent text-white border-brand-accent'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'
              }`}
              title={isAlerted ? 'Bấm để sửa cảnh báo giá' : 'Nhận thông báo khi giảm giá'}
            >
              <Bell size={16} fill={isAlerted ? 'currentColor' : 'none'} />
            </button>

            <button onClick={() => onAddWishlist(currentPlatformData)} className={`h-9 w-9 flex items-center justify-center rounded-full border transition-colors ${isWishlisted ? 'bg-brand-primary text-white border-brand-primary' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'}`}>
              <Heart size={16} fill={isWishlisted ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12">

          {/* Loading Banner - khi chưa fetch đủ platforms */}
          {platformsLoading && (
            <div className="col-span-full p-4 bg-blue-50 dark:bg-blue-950/30 border-b border-blue-200 dark:border-blue-900/50">
              <div className="flex items-center gap-3 text-blue-800 dark:text-blue-200">
                <Loader2 size={18} className="animate-spin" />
                <span className="text-sm font-bold">Đang tải dữ liệu từ các sàn...</span>
              </div>
            </div>
          )}

          {/* 2. Cột trái: Ảnh & Thông tin cơ bản */}
          <div className="p-8 md:p-12 lg:col-span-5 border-b lg:border-b-0 lg:border-r border-slate-100 dark:border-slate-800">
            <div className="mb-10 aspect-square overflow-hidden rounded-[2rem] bg-white dark:bg-slate-800 shadow-xl flex items-center justify-center p-8 border border-slate-100 dark:border-slate-700">
              {productImage && !imgError ? (
                <img
                  src={productImage}
                  alt={productName}
                  className="h-full w-full object-contain"
                  referrerPolicy="no-referrer"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="flex flex-col items-center justify-center gap-4 text-slate-300 dark:text-slate-600 w-full h-full">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                  </svg>
                  <span className="text-xs font-bold uppercase tracking-widest">Không có ảnh</span>
                </div>
              )}
            </div>

            {analysis && (
              <div className={`mb-4 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.1em] border shadow-sm ${getStatusStyles(analysis.deal_status)}`}>
                <Zap size={12} className="fill-current" />
                {analysis.deal_label}
              </div>
            )}

            <h1 className="mb-6 text-3xl font-black uppercase tracking-tighter text-slate-950 dark:text-white font-display leading-tight">
              {productName}
            </h1>

            <div className="mb-8 flex flex-wrap gap-4">
              <div className="flex items-center gap-2 rounded-xl bg-amber-50 dark:bg-amber-950/20 px-3 py-1.5 border border-amber-200/20">
                <Star size={16} className="fill-amber-400 text-amber-400" />
                <span className="text-sm font-black text-amber-700 dark:text-amber-400">{currentPlatformData.rating || '0.0'}</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 border border-slate-200/40">
                <Package size={16} className="text-slate-500" />
                <span className={`text-sm font-black ${currentPlatformData.in_stock ? 'text-brand-success' : 'text-rose-500'}`}>
                  {currentPlatformData.in_stock ? t('inStock') : t('outOfStock')}
                </span>
              </div>
            </div>

            {/* Deal Analysis Box */}
            <div className={`mb-8 rounded-[2rem] p-7 text-white shadow-2xl relative overflow-hidden transition-all duration-500 ${analysis?.deal_status === 'fake'
                ? 'bg-amber-950/40 border border-amber-500/30'
                : 'bg-slate-900 border border-white/5'
              }`}>
              <div className="relative z-10">
                <div className="mb-6 flex items-center justify-between">
                  <h3 className="flex items-center gap-2 text-[10px] font-black uppercase text-brand-primary font-display tracking-widest">
                    <Zap size={16} className="fill-brand-primary" /> {t('dealAnalysis')}
                  </h3>
                  {analysis && (
                    <span className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-tighter border ${getStatusStyles(analysis.deal_status)}`}>
                      {analysis.deal_label}
                    </span>
                  )}
                </div>

                <div className="space-y-5">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Giá hiện tại</span>
                    <span className="font-mono text-2xl font-black text-brand-success tracking-tighter">{formatPrice(currentPrice)}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Thấp nhất lịch sử</span>
                    <span className="font-mono text-xl font-black text-white/90">
                      {analysis ? formatPrice(analysis.lowest_ever_price) : formatPrice(currentPrice)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Trung bình 30 ngày</span>
                    <span className="font-mono text-xl font-black text-white/90">
                      {analysis ? formatPrice(analysis.avg_price_30d) : formatPrice(currentPrice)}
                    </span>
                  </div>
                  <div className="pt-2">
                    <p className="text-[11px] font-bold text-slate-300 leading-relaxed italic">
                      {analysis?.deal_status === 'fake'
                        ? "⚠️ Sản phẩm có dấu hiệu nâng giá ảo. Hãy kiểm tra biểu đồ bên dưới."
                        : analysis?.deal_status === 'extreme'
                          ? "🚀 Rẻ vô đối! Đây là mức giá thấp nhất từng ghi nhận được."
                          : "ℹ️ Giá cả đang ở mức ổn định so với lịch sử niêm yết."}
                    </p>
                  </div>
                </div>
              </div>
              <Zap size={140} className="absolute -bottom-10 -right-10 text-white/5 rotate-12 pointer-events-none" />
            </div>
          </div>

          {/* 3. Cột phải: So sánh & Lịch sử */}
          <div className="p-8 md:p-12 lg:col-span-7 bg-white dark:bg-slate-950">
            <section className="mb-12">
              <h2 className="mb-8 flex items-center gap-3 text-2xl font-black uppercase text-slate-950 dark:text-white font-display">
                <ShoppingCart size={24} className="text-brand-primary" />
                {t('comparePlatforms')}
              </h2>
              
              {/* Loading State */}
              {platformsLoading && (
                <div className="p-6 rounded-3xl bg-slate-100/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex items-center gap-3">
                  <Loader2 size={20} className="animate-spin text-brand-primary" />
                  <span className="text-sm font-bold text-slate-600 dark:text-slate-300">Đang tải dữ liệu giá từ các sàn...</span>
                </div>
              )}
              
              {/* Platform Selector - chỉ show khi đã load xong */}
              {!platformsLoading && allPlatformProducts.length > 0 && (
              <div className="relative mb-6">
                <button
                  onClick={() => setShowPlatformSelector(!showPlatformSelector)}
                  className="w-full p-6 rounded-3xl bg-brand-primary/5 border border-brand-primary/20 flex items-center justify-between hover:border-brand-primary/40 transition-colors"
                >
                  <div className="flex items-center gap-5">
                    <div className={`h-12 w-12 flex items-center justify-center rounded-xl text-white font-bold text-xl bg-gradient-to-br ${currentPlatformData.platform_id === 7 ? 'from-[#ee4d2d] to-[#d63f1f]' : currentPlatformData.platform_id === 1 ? 'from-[#ee4d2d] to-[#d63f1f]' : 'from-[#003da5] to-[#001f5c]'}`}>
                      {platformName.charAt(0)}
                    </div>
                    <div className="text-left">
                      <span className="text-lg font-black text-slate-950 dark:text-white font-display block">{platformName}</span>
                      <p className="text-[11px] font-bold text-slate-400">Giá: {formatPrice(currentPrice)}</p>
                    </div>
                  </div>
                  <ChevronDown size={20} className={`text-slate-500 transition-transform ${showPlatformSelector ? 'rotate-180' : ''}`} />
                </button>

                {/* Platform Options Dropdown */}
                {showPlatformSelector && allPlatformProducts.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-3xl shadow-xl z-50 overflow-hidden"
                  >
                    {allPlatformProducts.map((platform) => (
                      <button
                        key={platform.id}
                        onClick={() => handleSelectPlatform(platform)}
                        className={`w-full px-6 py-4 text-left border-b border-slate-100 dark:border-slate-800 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-between ${selectedPlatformProduct?.id === platform.id ? 'bg-brand-primary/10' : ''}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`h-10 w-10 flex items-center justify-center rounded-lg text-white font-bold text-sm bg-gradient-to-br ${platform.platform_id === 7 ? 'from-[#ee4d2d] to-[#d63f1f]' : platform.platform_id === 1 ? 'from-[#ee4d2d] to-[#d63f1f]' : 'from-[#003da5] to-[#001f5c]'}`}>
                            {getPlatformName(platform.platform_id).charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <span className="block font-bold text-slate-950 dark:text-white">{getPlatformName(platform.platform_id)}</span>
                            {platform.raw_name && (
                              <span className="block text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[420px]">{platform.raw_name}</span>
                            )}
                            <span className="block text-[11px] text-slate-500 dark:text-slate-400">{formatPrice(Number(platform.current_price) || 0)}</span>
                          </div>
                        </div>
                        {selectedPlatformProduct?.id === platform.id && (
                          <CheckCircle2 size={20} className="text-brand-primary" />
                        )}
                      </button>
                    ))}
                  </motion.div>
                )}
              </div>
              )}

              {/* Current Platform Info */}
              {!platformsLoading && allPlatformProducts.length > 0 && (
              <div className="p-6 ">
                
                <a href={currentPlatformData.url} target="_blank" rel="noopener noreferrer" className="bg-brand-primary text-white px-6 py-3 rounded-xl text-[10px] font-black uppercase text-center transition-opacity hover:opacity-90 flex-shrink-0">
                  {t('goToSeller')}
                </a>
              </div>
              )}
            </section>

            <section>
              <div className="mb-8 flex items-center justify-between">
                <h2 className="text-2xl font-black uppercase text-slate-950 dark:text-white font-display">{t('priceHistory6Months')}</h2>
              </div>
              <div className="relative rounded-[2rem] bg-slate-50/40 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 h-[400px] w-full overflow-hidden">
                {loading ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p className="italic text-slate-400 animate-pulse text-sm">Đang tải...</p>
                  </div>
                ) : historyData.length > 0 ? (
                  <div className="h-full w-full p-6">
                    <PriceChart data={historyData} />
                  </div>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p className="text-slate-400 text-sm">Chưa có dữ liệu lịch sử giá.</p>
                  </div>
                )}
              </div>
            </section>
          </div> 
        </div> 
      </div>

      {/* PORTAL: MODAL CẢNH BÁO GIÁ */}
      {isAlertModalOpen && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" 
            onClick={() => setIsAlertModalOpen(false)}
          />
          
          <div className="relative w-full max-w-sm rounded-[2rem] bg-white dark:bg-slate-900 p-8 shadow-2xl border border-slate-200/50 dark:border-slate-800/50 animate-in fade-in zoom-in-95 duration-200">
            <button 
              onClick={() => setIsAlertModalOpen(false)}
              className="absolute right-4 top-4 rounded-full p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X size={18} />
            </button>
            
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-accent/10 text-brand-accent">
                <Bell size={20} />
              </div>
              <h3 className="text-xl font-black font-display uppercase tracking-tight text-slate-900 dark:text-white">
                Cảnh báo giá
              </h3>
            </div>

            <p className="mb-4 text-sm font-medium text-slate-500 dark:text-slate-400">
              Theo dõi <strong>{currentPlatformData.raw_name}</strong>. Chúng tôi sẽ gửi email ngay khi giá giảm xuống mức này.
            </p>

            <div className="relative mb-8 group">
              <input
                type="text"
                value={targetPriceInput}
                onChange={handlePriceChange}
                placeholder={`VD: ${formatPrice(currentPrice - 500000).replace(/\D/g, '')}`}
                className="w-full rounded-xl border-0 bg-slate-50 dark:bg-slate-950/50 py-4 pl-5 pr-12 text-lg font-black text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all focus:bg-white focus:ring-2 focus:ring-brand-accent outline-none font-mono"
              />
              <span className="absolute right-5 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">
                ₫
              </span>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSaveAlert}
                disabled={isSubmittingAlert || !targetPriceInput}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-brand-accent py-4 text-xs font-black uppercase tracking-widest text-white shadow-xl shadow-brand-accent/20 transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none font-display"
              >
                {isSubmittingAlert ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  "Xác nhận đặt thông báo"
                )}
              </button>
              
              {isAlerted && (
                <button
                  onClick={async () => {
                    try {
                      await removeAlert?.(targetProductId);
                      showToast('Đã xóa cảnh báo giá!', 'success');
                      setIsAlertModalOpen(false);
                      setTargetPriceInput('');
                    } catch (error) {
                      showToast('Không thể xóa cảnh báo giá', 'error');
                    }
                  }}
                  className="flex items-center justify-center gap-2 rounded-xl bg-rose-50 dark:bg-rose-950/30 px-4 py-4 text-xs font-black uppercase tracking-widest text-rose-500 shadow-sm border border-rose-200 dark:border-rose-900 transition-all hover:bg-rose-100 dark:hover:bg-rose-900/50 active:scale-95 font-display"
                  title="Xóa cảnh báo giá này"
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
