import React, { useState } from 'react';
import { Product, PlatformData } from '../data/mockData';
import { PriceChart } from './PriceChart';
import { ArrowLeft, ExternalLink, Star, Bell, Heart, AlertTriangle, CheckCircle2, TrendingDown } from 'lucide-react';
import { motion } from 'motion/react';

interface ProductDetailProps {
  product: Product;
  onBack: () => void;
  onAddWishlist: (product: Product) => void;
  onSetAlert: (product: Product, threshold: number) => void;
  isWishlisted: boolean;
}

export function ProductDetail({ product, onBack, onAddWishlist, onSetAlert, isWishlisted }: ProductDetailProps) {
  const [alertThreshold, setAlertThreshold] = useState<string>('');
  const [alertSet, setAlertSet] = useState(false);

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
  };

  const handleSetAlert = () => {
    const threshold = parseInt(alertThreshold.replace(/[^0-9]/g, ''), 10);
    if (!isNaN(threshold) && threshold > 0) {
      onSetAlert(product, threshold);
      setAlertSet(true);
      setTimeout(() => setAlertSet(false), 3000);
    }
  };

  const sortedPlatforms = [...product.platforms].sort((a, b) => a.price - b.price);
  const bestPlatform = sortedPlatforms[0];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.98 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-zinc-200/50"
    >
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-zinc-100 bg-white/80 p-4 backdrop-blur-xl">
        <button 
          onClick={onBack}
          className="group flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium text-zinc-500 transition-all hover:bg-zinc-100 hover:text-zinc-900"
        >
          <ArrowLeft size={16} className="transition-transform group-hover:-translate-x-1" />
          Quay lại
        </button>
        <div className="flex gap-2">
          <button 
            onClick={() => onAddWishlist(product)}
            className={`flex h-10 w-10 items-center justify-center rounded-xl transition-all ${isWishlisted ? 'bg-rose-50 text-rose-500 ring-1 ring-rose-200' : 'bg-zinc-50 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600'}`}
          >
            <Heart size={18} fill={isWishlisted ? 'currentColor' : 'none'} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-0 lg:grid-cols-12">
        {/* Left Column: Image & Basic Info */}
        <div className="border-b border-zinc-100 bg-zinc-50/30 p-6 md:p-10 lg:col-span-4 lg:border-b-0 lg:border-r">
          <div className="mb-8 aspect-square overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-zinc-200/50">
            <img 
              src={product.image} 
              alt={product.name} 
              className="h-full w-full object-cover"
              referrerPolicy="no-referrer"
            />
          </div>
          
          <div>
            <div className="mb-3 inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-bold uppercase tracking-widest text-indigo-600 ring-1 ring-inset ring-indigo-500/10">
              {product.category}
            </div>
            <h1 className="mb-6 text-2xl font-bold leading-tight tracking-tight text-zinc-900">{product.name}</h1>
            
            {product.fakeDiscountDetected && (
              <div className="mb-8 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 ring-1 ring-inset ring-rose-600/10">
                <AlertTriangle className="mt-0.5 shrink-0 text-rose-600" size={18} />
                <div>
                  <h4 className="text-sm font-semibold text-rose-900">Cảnh báo giá ảo</h4>
                  <p className="mt-1 text-xs leading-relaxed text-rose-700/80">Sản phẩm này có dấu hiệu tăng giá trước khi giảm. Hãy xem biểu đồ lịch sử giá để quyết định.</p>
                </div>
              </div>
            )}

            <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-zinc-200/50">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-zinc-900">
                <Bell size={16} className="text-zinc-400" /> Nhận thông báo khi giá giảm
              </h3>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input 
                  type="text" 
                  placeholder="Nhập mức giá..." 
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(e.target.value)}
                  className="w-full rounded-xl border-0 bg-zinc-50 px-4 py-2.5 text-sm font-medium text-zinc-900 ring-1 ring-inset ring-zinc-200 transition-all placeholder:text-zinc-400 focus:bg-white focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                />
                <button 
                  onClick={handleSetAlert}
                  className="flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-zinc-800 active:scale-95 sm:w-auto"
                >
                  {alertSet ? <><CheckCircle2 size={16} className="text-emerald-400" /> Đã đặt</> : 'Đặt báo giá'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Comparison & History */}
        <div className="p-6 md:p-10 lg:col-span-8">
          
          {/* Price Comparison List */}
          <section className="mb-12">
            <h2 className="mb-6 flex items-center gap-2 text-lg font-bold tracking-tight text-zinc-900">
              So sánh giá các sàn
            </h2>
            <div className="flex flex-col gap-3">
              {sortedPlatforms.map((platform, idx) => {
                const isBest = idx === 0;
                return (
                  <div 
                    key={platform.name} 
                    className={`group flex flex-col justify-between gap-4 rounded-2xl p-4 transition-all sm:flex-row sm:items-center ${
                      isBest 
                        ? 'bg-emerald-50/50 ring-1 ring-emerald-200' 
                        : 'bg-white ring-1 ring-zinc-200 hover:bg-zinc-50 hover:ring-zinc-300'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl font-bold text-white shadow-sm
                        ${platform.name === 'Shopee' ? 'bg-orange-500' : platform.name === 'Lazada' ? 'bg-indigo-600' : 'bg-blue-500'}
                      `}>
                        {platform.name[0]}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-zinc-900">{platform.name}</span>
                          {isBest && <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-700">Rẻ nhất</span>}
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                          <div className="flex items-center gap-1">
                            <Star size={12} className="fill-amber-400 text-amber-400" />
                            <span className="font-medium text-zinc-700">{platform.rating}</span>
                            <span>({platform.reviews})</span>
                          </div>
                          <span className="h-3 w-px bg-zinc-300"></span>
                          <span>{platform.shippingFee === 0 ? <span className="font-medium text-emerald-600">Freeship</span> : `Ship: ${formatPrice(platform.shippingFee)}`}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between sm:justify-end sm:gap-6">
                      <div className="flex flex-col text-right">
                        <span className={`font-mono text-lg font-bold tracking-tight ${isBest ? 'text-emerald-600' : 'text-zinc-900'}`}>
                          {formatPrice(platform.price)}
                        </span>
                        {platform.originalPrice > platform.price && (
                          <span className="font-mono text-xs text-zinc-400 line-through">
                            {formatPrice(platform.originalPrice)}
                          </span>
                        )}
                      </div>
                      <a 
                        href={platform.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className={`flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all active:scale-95 ${
                          isBest 
                            ? 'bg-emerald-600 text-white hover:bg-emerald-700' 
                            : 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200'
                        }`}
                      >
                        Tới nơi bán
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Price History Chart */}
          <section>
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-bold tracking-tight text-zinc-900">Lịch sử giá (6 tháng)</h2>
              <div className="flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600">
                <TrendingDown size={14} className="text-emerald-500" />
                Đang có xu hướng giảm
              </div>
            </div>
            <div className="rounded-2xl bg-white p-6 ring-1 ring-zinc-200/50">
              <PriceChart data={product.history} />
            </div>
          </section>

        </div>
      </div>
    </motion.div>
  );
}
