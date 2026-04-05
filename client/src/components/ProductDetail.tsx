// import React, { useEffect, useState, useMemo } from 'react';
// import { Product } from '../data/mockData';
// import { PriceChart } from './PriceChart';
// import { ArrowLeft, Star, Bell, Heart, AlertTriangle, CheckCircle2, TrendingDown, Info, ShoppingBag, Package, ShoppingCart, ExternalLink, Zap, Share2, ShieldCheck } from 'lucide-react';
// import { motion } from 'motion/react';
// import { useLanguage } from '../context/LanguageContext';
// import { useTheme } from '../context/ThemeContext';
// import { PriceRecord } from '../services/api';

// interface ProductDetailProps {
//   product: Product;
//   onBack: () => void;
//   onAddWishlist: (product: Product) => void;
//   onSetAlert: (product: Product, threshold: number) => void;
//   isWishlisted: boolean;
// }

// export function ProductDetail({ product, onBack, onAddWishlist, onSetAlert, isWishlisted }: ProductDetailProps) {
//   const { t, language } = useLanguage();
//   const { theme } = useTheme();
//   const [alertThreshold, setAlertThreshold] = useState<string>('');
//   const [alertSet, setAlertSet] = useState(false);
//   const [copied, setCopied] = useState(false);

//   const formatPrice = (value: number) => {
//     const locale = language === 'vi' ? 'vi-VN' : 'en-US';
//     const currency = language === 'vi' ? 'VND' : 'USD';
//     const convertedValue = language === 'en' ? value / 25000 : value;
//     return new Intl.NumberFormat(locale, { 
//       style: 'currency', 
//       currency: currency,
//       maximumFractionDigits: language === 'en' ? 2 : 0
//     }).format(convertedValue);
//   };

//   const handleSetAlert = () => {
//     const threshold = parseInt(alertThreshold.replace(/[^0-9]/g, ''), 10);
//     if (!isNaN(threshold) && threshold > 0) {
//       onSetAlert(product, threshold);
//       setAlertSet(true);
//       setTimeout(() => setAlertSet(false), 3000);
//     }
//   };

//   const sortedPlatforms = [...product.platforms].sort((a, b) => a.price - b.price);
//   const bestPlatform = sortedPlatforms[0];

//   const getPlatformStyle = (name: string) => {
//     switch(name.toLowerCase()) {
//       case 'shopee': return 'bg-[#ee4d2d] text-white';
//       case 'lazada': return 'bg-[#0f136d] text-white';
//       case 'tiki': return 'bg-[#1a94ff] text-white';
//       default: return 'bg-zinc-800 text-white';
//     }
//   };

//   const getRecommendation = () => {
//     if (product.fakeDiscountDetected) {
//       return {
//         type: 'warning',
//         title: t('cautionBuy'),
//         desc: t('cautionBuyDesc'),
//         icon: AlertTriangle,
//         color: 'text-rose-600',
//         bg: 'bg-rose-50 dark:bg-rose-900/10',
//         ring: 'ring-rose-600/10 dark:ring-rose-500/20'
//       };
//     }
//     if (product.isTrending) {
//       return {
//         type: 'good',
//         title: t('goldenTimeBuy'),
//         desc: t('goldenTimeBuyDesc'),
//         icon: CheckCircle2,
//         color: 'text-brand-success',
//         bg: 'bg-brand-success/5 dark:bg-brand-success/10',
//         ring: 'ring-brand-success/20 dark:ring-brand-success/30'
//       };
//     }
//     return {
//       type: 'neutral',
//       title: t('stablePrice'),
//       desc: t('stablePriceDesc'),
//       icon: Info,
//       color: 'text-brand-accent',
//       bg: 'bg-brand-accent/5 dark:bg-brand-accent/10',
//       ring: 'ring-brand-accent/20 dark:ring-brand-accent/30'
//     };
//   };

//   const rec = getRecommendation();

//   const isLowestEver = product.platforms.some(p => p.price <= product.lowestEverPrice);
//   const isDropping = product.lastPriceChange === 'down';

//   return (
//     <motion.div 
//       initial={{ opacity: 0, y: 20, scale: 0.99 }}
//       animate={{ opacity: 1, y: 0, scale: 1 }}
//       exit={{ opacity: 0, y: -20, scale: 0.99 }}
//       transition={{ type: "spring", damping: 25, stiffness: 300 }}
//       className="overflow-hidden rounded-[2.5rem] bg-white dark:bg-slate-900 shadow-[0_30px_60px_rgba(0,0,0,0.08)] dark:shadow-[0_30px_60px_rgba(0,0,0,0.4)] border border-slate-200/60 dark:border-slate-800/60"
//     >
//       <div className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-100/50 dark:border-slate-800/50 bg-white/80 dark:bg-slate-900/80 p-4 backdrop-blur-xl">
//         <motion.button 
//           whileHover={{ x: -2 }}
//           whileTap={{ scale: 0.95 }}
//           onClick={onBack}
//           className="group flex items-center gap-2 rounded-full px-4 py-2 text-[10px] font-black text-slate-500 transition-all hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-950 dark:hover:text-slate-100 border border-slate-200/50 dark:border-slate-700/50 font-display uppercase tracking-[0.2em]"
//         >
//           <ArrowLeft size={14} className="transition-transform group-hover:-translate-x-0.5" />
//           {t('back')}
//         </motion.button>
//         <div className="flex gap-2">
//           <motion.button 
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.9 }}
//             onClick={() => {
//               navigator.clipboard.writeText(window.location.href);
//               setCopied(true);
//               setTimeout(() => setCopied(false), 2000);
//             }}
//             className="relative flex h-9 w-9 items-center justify-center rounded-full bg-slate-50 dark:bg-slate-800 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-950 dark:hover:text-slate-300 shadow-sm border border-slate-200/50 dark:border-slate-700/50"
//           >
//             <Share2 size={16} />
//             {copied && (
//               <motion.div 
//                 initial={{ opacity: 0, y: 8 }}
//                 animate={{ opacity: 1, y: 0 }}
//                 exit={{ opacity: 0 }}
//                 className="absolute -bottom-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-950 px-2.5 py-1 text-[9px] font-black text-white shadow-lg"
//               >
//                 Copied!
//               </motion.div>
//             )}
//           </motion.button>
//           <motion.button 
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.9 }}
//             onClick={() => onAddWishlist(product)}
//             className={`flex h-9 w-9 items-center justify-center rounded-full transition-all shadow-sm border ${isWishlisted ? 'bg-brand-primary text-white border-brand-primary/50' : 'bg-slate-50 dark:bg-slate-800 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-950 dark:hover:text-slate-300 border-slate-200/50 dark:border-slate-700/50'}`}
//           >
//             <Heart size={16} fill={isWishlisted ? 'currentColor' : 'none'} />
//           </motion.button>
//         </div>
//       </div>

//       <div className="grid grid-cols-1 gap-0 lg:grid-cols-12">
//         {/* Left Column: Image & Basic Info */}
//         <div className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/20 dark:bg-slate-900/20 p-8 md:p-12 lg:col-span-5 lg:border-b-0 lg:border-r lg:border-slate-100 dark:lg:border-slate-800">
//           <motion.div 
//             initial={{ scale: 0.95, opacity: 0 }}
//             animate={{ scale: 1, opacity: 1 }}
//             transition={{ delay: 0.1 }}
//             className="mb-10 aspect-square overflow-hidden rounded-[2rem] bg-white dark:bg-slate-800 shadow-2xl border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-center p-8"
//           >
//             <motion.img 
//               src={product.image} 
//               alt={product.name} 
//               whileHover={{ scale: 1.05 }}
//               transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
//               className="h-full w-full object-contain mix-blend-multiply dark:mix-blend-normal"
//               referrerPolicy="no-referrer"
//             />
//           </motion.div>
          
//           <motion.div
//             initial={{ y: 15, opacity: 0 }}
//             animate={{ y: 0, opacity: 1 }}
//             transition={{ delay: 0.2 }}
//           >
//             <div className="mb-4 inline-flex items-center rounded-sm bg-brand-primary/10 px-2 py-1 text-[9px] font-black uppercase tracking-[0.25em] text-brand-primary border border-brand-primary/20 font-display">
//               {product.category}
//             </div>
//             <h1 className="mb-6 text-4xl font-black leading-[1.05] tracking-tighter text-slate-950 dark:text-white font-display uppercase">{product.name}</h1>
            
//             <div className="mb-8 flex flex-wrap gap-4">
//               <div className="flex items-center gap-2 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 px-3 py-1.5 border border-amber-200/20 dark:border-amber-500/10 backdrop-blur-sm">
//                 <Star size={16} className="fill-amber-400 text-amber-400" />
//                 <span className="text-sm font-black text-amber-700 dark:text-amber-400">{product.rating}</span>
//                 <span className="text-[10px] font-bold text-amber-600/50 dark:text-amber-400/50">({product.reviewsCount})</span>
//               </div>
//               <div className="flex items-center gap-2 rounded-xl bg-slate-100/60 dark:bg-slate-800/60 px-3 py-1.5 border border-slate-200/40 dark:border-slate-700/40 backdrop-blur-sm">
//                 <Package size={16} className="text-slate-500" />
//                 <span className={`text-sm font-black ${product.stockStatus === 'in-stock' ? 'text-brand-success' : 'text-rose-500'}`}>
//                   {product.stockStatus === 'in-stock' ? t('inStock') : t('outOfStock')}
//                 </span>
//               </div>
//             </div>

//             {/* Recommendation Badge */}
//             <motion.div 
//               initial={{ x: -15, opacity: 0 }}
//               animate={{ x: 0, opacity: 1 }}
//               transition={{ delay: 0.3 }}
//               className={`mb-8 flex items-start gap-4 rounded-[1.5rem] p-5 shadow-xl border ${rec.bg} ${rec.ring.replace('ring-', 'border-')}`}
//             >
//               <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/90 dark:bg-slate-900/90 shadow-md border border-white/20 dark:border-slate-800/50 ${rec.color}`}>
//                 <rec.icon size={24} className={rec.type === 'warning' ? 'animate-pulse' : ''} />
//               </div>
//               <div>
//                 <h4 className={`text-base font-black font-display uppercase tracking-tight ${rec.color.replace('text-', 'text-').replace('600', '950')}`}>{rec.title}</h4>
//                 <p className={`mt-1 text-[11px] font-bold leading-relaxed opacity-80 ${rec.color.replace('text-', 'text-').replace('600', '700')}`}>{rec.desc}</p>
//               </div>
//             </motion.div>

//             {/* Deal Analysis Box */}
//             <motion.div
//               initial={{ y: 15, opacity: 0 }}
//               animate={{ y: 0, opacity: 1 }}
//               transition={{ delay: 0.35 }}
//               className="mb-8 overflow-hidden rounded-[1.5rem] bg-gradient-to-br from-slate-900 via-brand-dark to-slate-900 p-[1px] text-white shadow-2xl shadow-brand-primary/10"
//             >
//               <div className="rounded-[1.45rem] bg-slate-900/80 p-7 backdrop-blur-2xl">
//                 <div className="mb-6 flex items-center justify-between">
//                   <h3 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-brand-primary font-display">
//                     <Zap size={16} className="fill-brand-primary" /> {t('dealAnalysis')}
//                   </h3>
//                   {isLowestEver && (
//                     <span className="animate-bounce rounded-full bg-brand-success px-4 py-1.5 text-[8px] font-black uppercase tracking-widest text-white shadow-lg shadow-brand-success/30">
//                       {t('lowestEver')}
//                     </span>
//                   )}
//                 </div>
                
//                 <div className="space-y-5">
//                   <div className="flex items-center justify-between border-b border-white/10 pb-5">
//                     <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{t('lowestEver')}</span>
//                     <span className="font-mono text-2xl font-black text-brand-success tracking-tighter">{formatPrice(product.lowestEverPrice)}</span>
//                   </div>
                  
//                   <div className="flex items-center gap-4">
//                     <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border ${isDropping ? 'bg-brand-success/20 text-brand-success border-brand-success/30 shadow-lg shadow-brand-success/5' : 'bg-slate-800/50 text-slate-400 border-slate-700/50'}`}>
//                       <TrendingDown size={24} />
//                     </div>
//                     <p className="text-[11px] font-bold leading-relaxed text-slate-300">
//                       {isDropping ? t('buyNowStimulus') : t('waitStimulus')}
//                     </p>
//                   </div>
//                 </div>
//               </div>
//             </motion.div>

//             <div className="rounded-[1.5rem] bg-white dark:bg-slate-800 p-6 shadow-2xl shadow-slate-200/10 dark:shadow-black/10 border border-slate-200/60 dark:border-slate-700/60">
//               <h3 className="mb-5 flex items-center gap-2 text-[10px] font-black text-slate-900 dark:text-white uppercase tracking-widest font-display">
//                 <Bell size={16} className="text-brand-primary" /> {t('notifyPriceDrop')}
//               </h3>
//               <div className="flex flex-col gap-3">
//                 <div className="relative group">
//                   <span className="absolute inset-y-0 left-5 flex items-center font-mono text-sm font-black text-slate-400 group-focus-within:text-brand-primary transition-colors">₫</span>
//                   <input 
//                     type="text" 
//                     placeholder={t('enterPrice')}
//                     value={alertThreshold}
//                     onChange={(e) => setAlertThreshold(e.target.value)}
//                     className="w-full rounded-xl border-0 bg-slate-50 dark:bg-slate-900 py-4 pl-10 pr-5 text-sm font-black text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-slate-700 transition-all placeholder:text-slate-400 focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-inset focus:ring-brand-primary outline-none shadow-inner"
//                   />
//                 </div>
//                 <motion.button 
//                   whileHover={{ scale: 1.01 }}
//                   whileTap={{ scale: 0.99 }}
//                   onClick={handleSetAlert}
//                   className="flex items-center justify-center gap-2 rounded-xl bg-slate-900 dark:bg-brand-primary px-6 py-4 text-[11px] font-black text-white shadow-xl transition-all hover:bg-slate-800 dark:hover:bg-brand-primary/90 uppercase tracking-widest"
//                 >
//                   {alertSet ? <><CheckCircle2 size={18} className="text-brand-success" /> {t('priceAlertSet')}</> : t('setPriceAlert')}
//                 </motion.button>
//               </div>
//             </div>

//             <div className="mt-8 grid grid-cols-2 gap-4">
//               <div className="flex items-center gap-3 rounded-2xl bg-slate-50/60 dark:bg-slate-800/40 p-4 border border-slate-200/40 dark:border-slate-700/40 backdrop-blur-sm">
//                 <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
//                   <ShieldCheck size={20} />
//                 </div>
//                 <div>
//                   <p className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400">Verified</p>
//                   <p className="text-[11px] font-bold text-slate-600 dark:text-slate-300">Data Source</p>
//                 </div>
//               </div>
//               <div className="flex items-center gap-3 rounded-2xl bg-slate-50/60 dark:bg-slate-800/40 p-4 border border-slate-200/40 dark:border-slate-700/40 backdrop-blur-sm">
//                 <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-success/10 text-brand-success border border-brand-success/20">
//                   <Zap size={20} />
//                 </div>
//                 <div>
//                   <p className="text-[8px] font-black uppercase tracking-[0.2em] text-slate-400">Real-time</p>
//                   <p className="text-[11px] font-bold text-slate-600 dark:text-slate-300">Price Updates</p>
//                 </div>
//               </div>
//             </div>
//           </motion.div>
//         </div>

//         {/* Right Column: Comparison & History */}
//         <div className="p-8 md:p-12 lg:col-span-7 bg-white dark:bg-slate-950">
          
//           {/* Price Comparison List */}
//           <section className="mb-12">
//             <h2 className="mb-8 flex items-center gap-3 text-2xl font-black tracking-tight text-slate-950 dark:text-white font-display uppercase">
//               <ShoppingCart size={24} className="text-brand-primary" />
//               {t('comparePlatforms')}
//             </h2>
//             <div className="flex flex-col gap-4">
//               {sortedPlatforms.map((platform, idx) => {
//                 const isBest = idx === 0;
//                 return (
//                   <motion.div 
//                     key={platform.name} 
//                     initial={{ x: 15, opacity: 0 }}
//                     animate={{ opacity: 1, x: 0 }}
//                     transition={{ delay: 0.4 + idx * 0.05 }}
//                     whileHover={{ x: 4 }}
//                     className={`group flex flex-col justify-between gap-5 rounded-[1.5rem] p-6 transition-all sm:flex-row sm:items-center border ${
//                       isBest 
//                         ? 'bg-brand-primary/5 dark:bg-brand-primary/10 border-brand-primary/20 shadow-sm' 
//                         : 'bg-slate-50/40 dark:bg-slate-900/40 border-slate-200/50 dark:border-slate-800/50 hover:bg-white dark:hover:bg-slate-800 hover:shadow-xl'
//                     }`}
//                   >
//                     <div className="flex items-center gap-5">
//                       <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl font-black text-white shadow-lg border border-white/10 ${getPlatformStyle(platform.name)}`}>
//                         {platform.name === 'Shopee' ? <ShoppingBag size={20} /> : <span className="text-xl">{platform.name[0]}</span>}
//                       </div>
//                       <div>
//                         <div className="flex items-center gap-2">
//                           <span className="text-lg font-black text-slate-950 dark:text-white font-display">{platform.name}</span>
//                           {isBest && <span className="rounded-full bg-brand-success px-2.5 py-0.5 text-[8px] font-black uppercase tracking-widest text-white">{t('cheapest')}</span>}
//                         </div>
//                         <div className="mt-1 flex flex-wrap items-center gap-4 text-[11px] font-bold text-slate-500 dark:text-slate-400">
//                           <div className="flex items-center gap-1.5 rounded-md bg-amber-50 dark:bg-amber-950/10 px-2 py-0.5">
//                             <Star size={12} className="fill-amber-400 text-amber-400" />
//                             <span className="text-slate-700 dark:text-amber-400">{platform.rating}</span>
//                           </div>
//                           <span className="h-3 w-px bg-slate-200 dark:bg-slate-800"></span>
//                           <span className="flex items-center gap-1.5">
//                             {platform.shippingFee === 0 ? <span className="text-brand-success font-black">{t('freeShipping')}</span> : `${t('shipping')}: ${formatPrice(platform.shippingFee)}`}
//                           </span>
//                         </div>
//                       </div>
//                     </div>
                    
//                     <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 sm:border-0 sm:pt-0 sm:justify-end sm:gap-8">
//                       <div className="flex flex-col text-left sm:text-right">
//                         <span className={`font-mono text-2xl font-black tracking-tighter ${isBest ? 'text-brand-primary' : 'text-slate-950 dark:text-white'}`}>
//                           {formatPrice(platform.price)}
//                         </span>
//                         {platform.originalPrice > platform.price && (
//                           <span className="mt-1 font-mono text-[11px] font-bold text-slate-400 dark:text-slate-500 line-through opacity-50">
//                             {formatPrice(platform.originalPrice)}
//                           </span>
//                         )}
//                       </div>
//                       <motion.a 
//                         href={platform.url} 
//                         target="_blank" 
//                         rel="noopener noreferrer"
//                         whileHover={{ scale: 1.02 }}
//                         whileTap={{ scale: 0.98 }}
//                         className={`flex items-center justify-center rounded-xl px-5 py-3 text-[10px] font-black transition-all border uppercase tracking-widest ${
//                           isBest 
//                             ? 'bg-brand-primary text-white border-brand-primary/40 hover:bg-brand-primary/90 shadow-2xl shadow-brand-primary/20' 
//                             : 'bg-white dark:bg-slate-800 text-slate-950 dark:text-white border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
//                         }`}
//                       >
//                         {t('goToSeller')}
//                         <ExternalLink size={14} className="ml-2 opacity-50" />
//                       </motion.a>
//                     </div>
//                   </motion.div>
//                 );
//               })}
//             </div>
//           </section>

//           {/* Price History Chart */}
//           <motion.section
//             initial={{ y: 20, opacity: 0 }}
//             animate={{ y: 0, opacity: 1 }}
//             transition={{ delay: 0.6 }}
//           >
//             <div className="mb-8 flex items-center justify-between">
//               <h2 className="text-2xl font-black tracking-tight text-slate-950 dark:text-white font-display uppercase tracking-tight">{t('priceHistory6Months')}</h2>
//               <div className="flex items-center gap-2 rounded-full bg-brand-success/10 px-4 py-2 text-[10px] font-black text-brand-success border border-brand-success/20 backdrop-blur-sm uppercase tracking-widest">
//                 <TrendingDown size={16} />
//                 {t('trendingDown')}
//               </div>
//             </div>
//             <div className="rounded-[2rem] bg-slate-50/40 dark:bg-slate-900/40 p-8 shadow-sm border border-slate-200/50 dark:border-slate-800/50 backdrop-blur-xl">
//               <PriceChart data={product.history} />
//             </div>
//           </motion.section>

//         </div>
//       </div>
//     </motion.div>
//   );
// }

// F:\dai_hoc\2526_Ki_2\CDCNNB\ProductHunter\client\src\components\ProductDetail.tsx

import React, { useEffect, useState } from 'react';
import { PriceChart } from './PriceChart';
import { ArrowLeft, Star, Bell, Heart, AlertTriangle, CheckCircle2, TrendingDown, Info, ShoppingBag, Package, ShoppingCart, ExternalLink, Zap, Share2, ShieldCheck } from 'lucide-react';
import { motion } from 'motion/react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { fetchPriceHistory } from '../services/api'; // Đảm bảo đã import hàm này

interface ProductDetailProps {
  platformProduct: any; // Nhận dữ liệu phẳng từ DB
  initialPlatformId: string; // ID dùng để truy vấn price_records
  onBack: () => void;
  onAddWishlist: (p: any) => void;
  onSetAlert: (product: any, threshold: number) => void; 
  isWishlisted: boolean;
}

export function ProductDetail({ platformProduct, initialPlatformId, onBack, onAddWishlist, onSetAlert, isWishlisted }: ProductDetailProps) {
  console.log("Dữ liệu nhận được trong Detail:", platformProduct);
  const { t, language } = useLanguage();
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  // 1. Ép kiểu dữ liệu từ DB (String -> Number)
  const currentPrice = parseFloat(platformProduct.current_price) || 0;
  const originalPrice = parseFloat(platformProduct.original_price) || 0;

  // 2. useEffect gọi API lấy lịch sử giá thật
  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      try {
        const data = await fetchPriceHistory(initialPlatformId);
        const formatted = data.map(record => ({
          date: new Date(record.recorded_at).toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US', {
            month: 'short',
            day: 'numeric'
          }),
          price: Number(record.price)
        }));
        setHistoryData(formatted);
      } catch (err) {
        console.error("Lỗi lấy lịch sử giá:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [initialPlatformId, language]);

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
      case 7: return 'Shopee';
      case 8: return 'Lazada';
      default: return 'Sàn khác';
    }
  };

  const platformName = getPlatformName(platformProduct.platform_id);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-[2.5rem] bg-white dark:bg-slate-900 shadow-2xl border border-slate-200/60 dark:border-slate-800/60"
    >
      {/* Header Buttons */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b p-4 backdrop-blur-xl bg-white/80 dark:bg-slate-900/80">
        <button onClick={onBack} className="flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase border rounded-full">
          <ArrowLeft size={14} /> {t('back')}
        </button>
        <div className="flex gap-2">
           <button onClick={() => onAddWishlist(platformProduct)} className={`h-9 w-9 flex items-center justify-center rounded-full border ${isWishlisted ? 'bg-brand-primary text-white' : ''}`}>
              <Heart size={16} fill={isWishlisted ? 'currentColor' : 'none'} />
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Cột trái: Ảnh & Thông tin cơ bản */}
        <div className="p-8 md:p-12 lg:col-span-5 border-r dark:border-slate-800">
          <div className="mb-10 aspect-square overflow-hidden rounded-[2rem] bg-white dark:bg-slate-800 shadow-xl flex items-center justify-center p-8">
            <img 
              src={platformProduct.main_image_url || "https://picsum.photos/seed/product/400/400"} 
              alt={platformProduct.raw_name} 
              className="h-full w-full object-contain"
            />
          </div>
          
          <div className="mb-4 inline-flex items-center rounded-sm bg-brand-primary/10 px-2 py-1 text-[9px] font-black uppercase text-brand-primary">
            {platformProduct.category || "Electronics"}
          </div>
          <h1 className="mb-6 text-3xl font-black uppercase tracking-tighter text-slate-950 dark:text-white font-display">
            {platformProduct.raw_name}
          </h1>
          
          <div className="mb-8 flex flex-wrap gap-4">
            <div className="flex items-center gap-2 rounded-xl bg-amber-50 dark:bg-amber-950/20 px-3 py-1.5 border border-amber-200/20">
              <Star size={16} className="fill-amber-400 text-amber-400" />
              <span className="text-sm font-black text-amber-700 dark:text-amber-400">{platformProduct.rating || '0.0'}</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 border border-slate-200/40">
              <Package size={16} className="text-slate-500" />
              <span className={`text-sm font-black ${platformProduct.in_stock ? 'text-brand-success' : 'text-rose-500'}`}>
                {platformProduct.in_stock ? t('inStock') : t('outOfStock')}
              </span>
            </div>
          </div>

          {/* Deal Analysis Box */}
          <div className="mb-8 rounded-[1.5rem] bg-slate-900 p-7 text-white shadow-2xl">
              <div className="mb-6 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-[10px] font-black uppercase text-brand-primary font-display">
                  <Zap size={16} className="fill-brand-primary" /> {t('dealAnalysis')}
                </h3>
              </div>
              <div className="flex items-center justify-between border-b border-white/10 pb-5">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Giá hiện tại</span>
                  <span className="font-mono text-2xl font-black text-brand-success tracking-tighter">{formatPrice(currentPrice)}</span>
              </div>
          </div>
        </div>

        {/* Cột phải: Lịch sử và Thông tin sàn */}
        <div className="p-8 md:p-12 lg:col-span-7 bg-white dark:bg-slate-950">
          <section className="mb-12">
            <h2 className="mb-8 flex items-center gap-3 text-2xl font-black uppercase text-slate-950 dark:text-white font-display">
              <ShoppingCart size={24} className="text-brand-primary" />
              {t('comparePlatforms')}
            </h2>
            
            {/* Vì dữ liệu phẳng, ta chỉ hiển thị 1 sàn duy nhất đã chọn */}
            <div className="p-6 rounded-[1.5rem] bg-brand-primary/5 border border-brand-primary/20 flex items-center justify-between">
              <div className="flex items-center gap-5">
                <div className="h-12 w-12 flex items-center justify-center bg-orange-500 rounded-xl text-white font-bold text-xl">
                  {platformName[0]}
                </div>
                <div>
                  <span className="text-lg font-black text-slate-950 dark:text-white font-display">{platformName}</span>
                  <p className="text-[11px] font-bold text-slate-400">Đang xem lịch sử giá tại sàn này</p>
                </div>
              </div>
              <a href={platformProduct.url} target="_blank" className="bg-brand-primary text-white px-5 py-3 rounded-xl text-[10px] font-black uppercase">
                {t('goToSeller')}
              </a>
            </div>
          </section>

          {/* Biểu đồ lịch sử giá thật */}
          <section>
            <div className="mb-8 flex items-center justify-between">
              <h2 className="text-2xl font-black uppercase text-slate-950 dark:text-white font-display">{t('priceHistory6Months')}</h2>
            </div>
            <div className="rounded-[2rem] bg-slate-50/40 dark:bg-slate-900/40 p-8 border min-h-[350px] flex items-center justify-center">
              {loading ? (
                <p className="italic text-slate-400 animate-pulse">Đang truy vấn lịch sử giá từ DB...</p>
              ) : historyData.length > 0 ? (
                <PriceChart data={historyData} />
              ) : (
                <p className="text-slate-400">Chưa có dữ liệu lịch sử giá cho sản phẩm này.</p>
              )}
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}