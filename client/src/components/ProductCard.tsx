import React from 'react';
import { Product } from '../data/mockData';
import { TrendingUp, AlertTriangle, CheckCircle2, Star, X, Heart } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { motion, AnimatePresence } from 'motion/react';

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

  const currentPrice = parseFloat(product.current_price) || 0;
  const originalPrice = parseFloat(product.original_price) || 0;

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

  // const lowestPricePlatform = product.platforms.reduce((prev, curr) => 
  //   prev.price < curr.price ? prev : curr
  // );
  const getPlatformName = (id: number) => {
    switch(id) {
      case 7: return 'FPT Shop'; // Ví dụ ID 7 trong ảnh của bạn là Shopee
      case 8: return 'Phong Vũ';
      default: return 'Sàn khác';
    }
  };

  const getPlatformColor = (name: string) => {
    switch(name.toLowerCase()) {
      case 'shopee': return 'bg-[#ee4d2d] text-white';
      case 'FPT Shop': return 'bg-[#ee4d2d] text-white';
      case 'Phong Vũ': return 'bg-[#0f136d] text-white';
      case 'lazada': return 'bg-[#0f136d] text-white';
      case 'tiki': return 'bg-[#1a94ff] text-white';
      default: return 'bg-slate-800 text-white';
    }
  };

  const platformName = getPlatformName(product.platform_id);

//   return (
//     <motion.div 
//       layout
//       initial={{ opacity: 0, y: 10 }}
//       animate={{ opacity: 1, y: 0 }}
//       whileHover={{ y: -6, transition: { duration: 0.3, ease: "easeOut" } }}
//       onClick={() => onClick(product)}
//       className="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 transition-all duration-300 hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] dark:hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)]"
//     >
//       {/* Action Buttons */}
//       <div className="absolute right-3 top-3 z-20 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
//         {onRemove && (
//           <motion.button
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.95 }}
//             onClick={(e) => {
//               e.stopPropagation();
//               onRemove(e, product);
//             }}
//             className="flex h-8 w-8 items-center justify-center rounded-full bg-white/95 dark:bg-slate-800/95 text-slate-400 shadow-sm backdrop-blur-md hover:text-rose-500 transition-colors border border-slate-100 dark:border-slate-700"
//           >
//             <X size={14} />
//           </motion.button>
//         )}
//         {!onRemove && onToggleWishlist && (
//           <motion.button
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.95 }}
//             onClick={(e) => {
//               e.stopPropagation();
//               onToggleWishlist(e, product);
//             }}
//             className={`flex h-8 w-8 items-center justify-center rounded-full shadow-sm backdrop-blur-md transition-all border ${
//               isWishlisted 
//                 ? 'bg-brand-primary text-white border-brand-primary' 
//                 : 'bg-white/95 dark:bg-slate-800/95 text-slate-400 hover:text-brand-primary border-slate-100 dark:border-slate-700'
//             }`}
//           >
//             <Heart size={14} fill={isWishlisted ? "currentColor" : "none"} />
//           </motion.button>
//         )}
//       </div>

//       {/* Image Section */}
//       <div className="relative aspect-[4/3] w-full overflow-hidden bg-white dark:bg-slate-800/50 flex items-center justify-center p-6 border-b border-slate-100 dark:border-slate-800/50">
//         <motion.img 
//           src={product.image} 
//           alt={product.name} 
//           whileHover={{ scale: 1.05 }}
//           transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
//           className="h-full w-full object-contain mix-blend-multiply dark:mix-blend-normal"
//           referrerPolicy="no-referrer"
//         />
        
//         {/* Badges */}
//         <div className="absolute left-3 top-3 flex flex-col gap-1 z-10">
//           {product.isTrending && (
//             <div className="flex w-fit items-center gap-1 rounded-sm bg-brand-primary px-1.5 py-0.5 text-[8px] font-black uppercase tracking-[0.1em] text-white shadow-lg shadow-brand-primary/20 font-display">
//               <TrendingUp size={9} strokeWidth={3} /> {t('trending')}
//             </div>
//           )}
//           {!product.fakeDiscountDetected && product.isTrending && (
//             <div className="flex w-fit items-center gap-1 rounded-sm bg-emerald-500 px-1.5 py-0.5 text-[8px] font-black uppercase tracking-[0.1em] text-white shadow-lg shadow-emerald-500/20 font-display">
//               <CheckCircle2 size={9} strokeWidth={3} /> {t('shouldBuy')}
//             </div>
//           )}
//         </div>

//         {lowestPricePlatform.originalPrice > lowestPricePlatform.price && (
//           <div className="absolute left-3 bottom-3 rounded-sm bg-slate-950/90 px-1.5 py-0.5 text-[9px] font-black text-white backdrop-blur-md font-mono tracking-tighter z-10">
//             -{Math.round((1 - lowestPricePlatform.price / lowestPricePlatform.originalPrice) * 100)}%
//           </div>
//         )}
//       </div>
      
//       {/* Content Section */}
//       <div className="flex flex-grow flex-col p-4">
//         <div className="mb-2 flex items-center justify-between">
//           <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 font-display">{product.category}</span>
//           <div className="flex items-center gap-0.5 text-amber-500">
//             <Star size={9} className="fill-current" />
//             <span className="text-[10px] font-bold text-slate-600 dark:text-slate-400">{product.rating}</span>
//           </div>
//         </div>

//         <h3 className="mb-4 line-clamp-2 text-[14px] font-bold leading-[1.3] text-slate-950 dark:text-white group-hover:text-brand-primary transition-colors font-display tracking-tight">
//           {product.name}
//         </h3>
        
//         <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/50">
//           <div className="flex items-end justify-between">
//             <div className="flex flex-col gap-1">
//               <span className="text-[8px] font-black uppercase tracking-[0.15em] text-slate-400 font-display">{t('bestPriceAt')}</span>
//               <span className={`w-fit rounded-sm px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider ${getPlatformColor(lowestPricePlatform.name)}`}>
//                 {lowestPricePlatform.name}
//               </span>
//             </div>
//             <div className="text-right">
//               <div className="font-mono text-lg font-black tracking-tighter text-brand-primary leading-none">
//                 {formatPrice(lowestPricePlatform.price)}
//               </div>
//               {lowestPricePlatform.originalPrice > lowestPricePlatform.price && (
//                 <div className="mt-1 font-mono text-[10px] font-medium text-slate-400 line-through leading-none">
//                   {formatPrice(lowestPricePlatform.originalPrice)}
//                 </div>
//               )}
//             </div>
//           </div>
          
//           {product.fakeDiscountDetected && (
//             <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-50 dark:bg-rose-950/30 px-2.5 py-2 text-[9px] font-bold text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-900/30">
//               <AlertTriangle size={11} className="shrink-0" />
//               <span className="leading-tight">{t('fakeDiscountWarning')}</span>
//             </div>
//           )}
//         </div>
//       </div>
//     </motion.div>
//   );
// }

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -6 }}
      onClick={() => onClick(product, product.id)}
      className="group relative flex h-full cursor-pointer flex-col overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 transition-all duration-300 hover:shadow-xl"
    >
      {/* Action Buttons */}
      <div className="absolute right-3 top-3 z-20 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300">
        {onRemove && (
          <button onClick={(e) => { e.stopPropagation(); onRemove(e, product); }} className="p-2 bg-white rounded-full text-slate-400 hover:text-rose-500 shadow-sm border border-slate-100">
            <X size={14} />
          </button>
        )}
      </div>

      {/* Image Section */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-white dark:bg-slate-800/50 flex items-center justify-center p-6 border-b border-slate-100 dark:border-slate-800/50">
        <motion.img 
          // Dùng ảnh từ DB, nếu không có dùng ảnh tạm
          src={product.main_image_url || `https://picsum.photos/seed/${product.id}/400/400`} 
          alt={product.raw_name} 
          whileHover={{ scale: 1.05 }}
          className="h-full w-full object-contain mix-blend-multiply dark:mix-blend-normal"
          referrerPolicy="no-referrer"
        />
        
        {/* Badges */}
        <div className="absolute left-3 top-3 flex flex-col gap-1 z-10">
          {product.in_stock && (
            <div className="flex w-fit items-center gap-1 rounded-sm bg-emerald-500 px-1.5 py-0.5 text-[8px] font-black uppercase text-white font-display">
              <CheckCircle2 size={9} strokeWidth={3} /> {t('inStock')}
            </div>
          )}
        </div>

        {/* Tính % giảm giá dựa trên current_price và original_price */}
        {originalPrice > currentPrice && (
          <div className="absolute left-3 bottom-3 rounded-sm bg-slate-950/90 px-1.5 py-0.5 text-[9px] font-black text-white backdrop-blur-md font-mono z-10">
            -{Math.round((1 - currentPrice / originalPrice) * 100)}%
          </div>
        )}
      </div>
      
      {/* Content Section */}
      <div className="flex flex-grow flex-col p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 font-display">Category</span>
          <div className="flex items-center gap-0.5 text-amber-500">
            <Star size={9} className="fill-current" />
            <span className="text-[10px] font-bold text-slate-600 dark:text-slate-400">{product.rating || '0.0'}</span>
          </div>
        </div>

        {/* Tên sản phẩm dùng raw_name */}
        <h3 className="mb-4 line-clamp-2 text-[14px] font-bold leading-[1.3] text-slate-950 dark:text-white group-hover:text-brand-primary font-display tracking-tight">
          {product.raw_name}
        </h3>
        
        <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/50">
          <div className="flex items-end justify-between">
            <div className="flex flex-col gap-1">
              <span className="text-[8px] font-black uppercase tracking-[0.15em] text-slate-400 font-display">Giá tại</span>
              <span className={`w-fit rounded-sm px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider ${getPlatformColor(platformName)}`}>
                {platformName}
              </span>
            </div>
            <div className="text-right">
              <div className="font-mono text-lg font-black tracking-tighter text-brand-primary leading-none">
                {formatPrice(currentPrice)}
              </div>
              {originalPrice > currentPrice && (
                <div className="mt-1 font-mono text-[10px] font-medium text-slate-400 line-through leading-none">
                  {formatPrice(originalPrice)}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}