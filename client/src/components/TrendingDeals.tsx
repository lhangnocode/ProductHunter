import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp } from 'lucide-react';
import { ProductCard } from './ProductCard';
import { useLanguage } from '../context/LanguageContext';
import { fetchTrendingDeals } from '../services/trending_deal_api';

// 1. Định nghĩa Interface dựa trên TrendingDealResponse từ Backend
interface TrendingDeal {
  id: string; // platform_product_id
  product_id: string;
  product_name: string;
  main_image_url: string;
  current_price: number;
  original_price?: number;
  url: string;
  deal_status: string;
  deal_label: string;
  platform_name?: string;
}

interface TrendingDealsProps {
  onProductClick: (product: TrendingDeal, id: string) => void;
  wishlistIds: Set<string>;
  onToggleWishlist: (product: TrendingDeal) => void;
}

export function TrendingDeals({ onProductClick, wishlistIds, onToggleWishlist }: TrendingDealsProps) {
  const { t } = useLanguage();
  
  const [deals, setDeals] = useState<TrendingDeal[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const getDeals = async () => {
      try {
        setIsLoading(true);
        const data = await fetchTrendingDeals();
        
        // Vì Backend đã xử lý cleanImageUrl và làm phẳng dữ liệu,
        // chúng ta có thể set trực tiếp hoặc chỉ cần xử lý fallback nhẹ.
        setDeals(data);
      } catch (error) {
        console.error("Lỗi khi tải Trending Deals:", error);
      } finally {
        setIsLoading(false);
      }
    };

    getDeals();
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { type: "spring" as const, stiffness: 260, damping: 20 } 
    }
  };

  return (
    <div className="space-y-10">
      {/* Header */}
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
          <span className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-primary mb-1 block font-display">
            Market Trends
          </span>
          <h2 className="text-3xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">
            {t('trendingDeals')}
          </h2>
          <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">
            {t('trendingSubtitle') || 'Săn ngay các sản phẩm rẻ kỷ lục và giá tốt nhất hôm nay'}
          </p>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 dark:border-slate-800 border-t-brand-primary" />
          <p className="text-sm font-bold text-slate-400 animate-pulse">Đang tìm kiếm deal cực hời...</p>
        </div>
      ) : deals.length === 0 ? (
        <div className="py-20 text-center text-slate-500">
          Không có deal nào nổi bật lúc này.
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {deals.map((product) => (
            <motion.div key={product.id} variants={itemVariants}>
              <ProductCard
                product={product}
                onClick={onProductClick}
                // Sử dụng product.product_id để check wishlist (vì wishlist thường lưu ID sản phẩm chung)
                isWishlisted={wishlistIds.has(product.product_id)}
                onToggleWishlist={(e) => {
                  e.stopPropagation();
                  onToggleWishlist(product);
                }}
              />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}