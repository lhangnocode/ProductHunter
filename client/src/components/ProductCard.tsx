import React, { useState, useEffect } from 'react';
import { formatDisplayName } from '../lib/utils';
import { createPortal } from 'react-dom'; // Bắt buộc dùng để popup hiển thị đè lên toàn trang
import { Star, CheckCircle2, X, Heart, Bell, Loader2 } from 'lucide-react';
import { motion } from 'motion/react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';
import { priceAlertService } from '../services/priceAlert';

interface ProductCardProps {
  product: any;
  onClick: (product: any, id: string) => void; 
  onRemove?: (e: React.MouseEvent, product: any) => void;
  onToggleWishlist?: (e: React.MouseEvent, product: any) => void;
  isWishlisted?: boolean;
  key?: React.Key;
}

export function ProductCard({ product, onClick, onRemove, onToggleWishlist, isWishlisted }: ProductCardProps) {
  const { t, language } = useLanguage();
  const { theme } = useTheme();
  
  // Lấy User và Toast để xử lý cảnh báo giá
  const { user } = useUser();
  const { showToast } = useToast();

  // State quản lý Modal Cảnh báo giá
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [targetPriceInput, setTargetPriceInput] = useState('');
  const [isSubmittingAlert, setIsSubmittingAlert] = useState(false);

  // Lọc URL mock không hợp lệ
  const isRealImageUrl = (url: string | null | undefined): boolean => {
    if (!url || typeof url !== 'string' || url.trim() === '') return false;
    const mockPatterns = ['picsum.photos', 'placeholder.com', 'placehold.co', 'loremflickr', 'dummyimage', 'via.placeholder'];
    return !mockPatterns.some(p => url.includes(p));
  };
  const productImage = isRealImageUrl(product.main_image_url) ? product.main_image_url : null;

  // State track lỗi ảnh — reset khi ảnh mới
  const [imgError, setImgError] = useState(false);
  useEffect(() => { setImgError(false); }, [productImage]);

  const currentPrice = parseFloat(product.current_price) || 0;
  const originalPrice = parseFloat(product.original_price) || 0;

  // Support compare-group shape: if product has `platforms`, use lowest_price as current
  const isGroup = Array.isArray(product.platforms);
  const displayPrice = isGroup ? (product.lowest_price ?? product.current_price ?? 0) : currentPrice;
  const displayOriginal = isGroup ? (product.original_price ?? product.lowest_price ?? 0) : originalPrice;

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
    switch(id) {
      case 7: return 'FPT Shop'; 
      case 8: return 'Phong Vũ';
      default: return 'Sàn khác';
    }
  };

  const getPlatformColor = (name: string) => {
    switch(name.toLowerCase()) {
      case 'shopee': return 'bg-[#ee4d2d] text-white';
      case 'fpt shop': return 'bg-[#ee4d2d] text-white';
      case 'phong vũ': return 'bg-[#0f136d] text-white';
      case 'lazada': return 'bg-[#0f136d] text-white';
      case 'tiki': return 'bg-[#1a94ff] text-white';
      default: return 'bg-slate-800 text-white';
    }
  };

  const platformName = getPlatformName(product.platform_id);

  // Hàm xử lý lưu cảnh báo giá
  const handleSaveAlert = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Ngăn click lan ra thẻ card
    const numericPrice = parseFloat(targetPriceInput.replace(/\D/g, ''));
    if (isNaN(numericPrice) || numericPrice <= 0) {
      showToast('Vui lòng nhập mức giá hợp lệ!', 'error');
      return;
    }

    setIsSubmittingAlert(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) throw new Error("Missing token");

      await priceAlertService.setAlert(token, product.id, numericPrice);
      
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
  // Use shared name formatter from utils

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        whileHover={{ y: -6 }}
        onClick={() => onClick(product, product.id)}
        className="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 transition-all duration-300 hover:shadow-xl"
      >
        {/* THÊM LẠI ACTION BUTTONS (Wishlist & Alert) */}
        <div className="absolute right-3 top-3 z-20 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
          {onRemove && (
            <button onClick={(e) => { e.stopPropagation(); onRemove(e, product); }} className="p-2 bg-white dark:bg-slate-800 rounded-full text-slate-400 hover:text-rose-500 shadow-sm border border-slate-100 dark:border-slate-700">
              <X size={14} />
            </button>
          )}

          {!onRemove && (
            <>
              {/* Nút Chuông (Alert) */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (!user) {
                    showToast('Vui lòng đăng nhập để đặt cảnh báo giá!', 'info');
                    return;
                  }
                  setIsAlertModalOpen(true);
                }}
                className="p-2 bg-white/95 dark:bg-slate-800/95 rounded-full text-slate-400 hover:text-brand-accent shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
                title="Nhận thông báo khi giảm giá"
              >
                <Bell size={14} />
              </button>

              {/* Nút Tim (Wishlist) */}
              {onToggleWishlist && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleWishlist(e, product);
                  }}
                  className={`p-2 rounded-full shadow-sm border transition-colors ${
                    isWishlisted 
                      ? 'bg-brand-primary text-white border-brand-primary' 
                      : 'bg-white/95 dark:bg-slate-800/95 text-slate-400 hover:text-brand-primary border-slate-100 dark:border-slate-700'
                  }`}
                  title="Thêm vào Wishlist"
                >
                  <Heart size={14} fill={isWishlisted ? "currentColor" : "none"} />
                </button>
              )}
            </>
          )}
        </div>

        {/* Image Section */}
        <div className="relative aspect-[4/3] w-full overflow-hidden bg-white dark:bg-slate-800/50 flex items-center justify-center p-6 border-b border-slate-100 dark:border-slate-800/50">
          {productImage && !imgError ? (
            <motion.img
              src={productImage}
              alt={product.raw_name}
              whileHover={{ scale: 1.05 }}
              className="h-full w-full object-contain mix-blend-multiply dark:mix-blend-normal"
              referrerPolicy="no-referrer"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 w-full h-full">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-primary/20 to-brand-primary/5 dark:from-brand-primary/30 dark:to-brand-primary/10 flex items-center justify-center border border-brand-primary/10 shadow-sm">
                <span className="text-2xl font-black text-brand-primary/60 dark:text-brand-primary/70 font-display uppercase select-none">
                  {(product.raw_name || product.slug || '?').charAt(0)}
                </span>
              </div>
              <p className="text-[9px] font-bold text-slate-300 dark:text-slate-600 uppercase tracking-widest">Chưa có ảnh</p>
            </div>
          )}

          
          <div className="absolute left-3 top-3 flex flex-col gap-1 z-10">
            {product.in_stock && (
              <div className="flex w-fit items-center gap-1 rounded-sm bg-emerald-500 px-1.5 py-0.5 text-[8px] font-black uppercase text-white font-display">
                <CheckCircle2 size={9} strokeWidth={3} /> {t('inStock')}
              </div>
            )}
          </div>

          {displayOriginal > displayPrice && displayPrice > 0 && (
            <div className="absolute left-3 bottom-3 rounded-sm bg-slate-950/90 px-1.5 py-0.5 text-[9px] font-black text-white backdrop-blur-md font-mono z-10">
              -{Math.round((1 - displayPrice / displayOriginal) * 100)}%
            </div>
          )}
        </div>
        
        {/* Content Section */}
        {/* Content Section */}
        <div className="flex flex-grow flex-col items-center justify-center p-4 text-center">
          <h3 className="line-clamp-2 text-[15px] font-bold leading-[1.4] text-slate-950 dark:text-white group-hover:text-brand-primary font-display tracking-tight">
            {formatDisplayName(product.product_name || product.slug || product.normalized_name || product.raw_name || '')}
          </h3>
        </div>
      </motion.div>
    
      {/* PORTAL: MODAL CẢNH BÁO GIÁ (Hiển thị đè lên trên tất cả) */}
      {isAlertModalOpen && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" 
            onClick={(e) => { e.stopPropagation(); setIsAlertModalOpen(false); }}
          />
          
          <div 
            className="relative w-full max-w-sm rounded-[2rem] bg-white dark:bg-slate-900 p-8 shadow-2xl border border-slate-200/50 dark:border-slate-800/50"
            onClick={(e) => e.stopPropagation()} // Chặn click xuyên qua nền
          >
            <button 
              onClick={(e) => { e.stopPropagation(); setIsAlertModalOpen(false); }}
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
              Theo dõi <strong>{product.raw_name}</strong>. Chúng tôi sẽ gửi email ngay khi giá giảm xuống mức này.
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

            <button
              onClick={handleSaveAlert}
              disabled={isSubmittingAlert || !targetPriceInput}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-accent py-4 text-xs font-black uppercase tracking-widest text-white shadow-xl shadow-brand-accent/20 transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none font-display"
            >
              {isSubmittingAlert ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                "Xác nhận đặt thông báo"
              )}
            </button>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
