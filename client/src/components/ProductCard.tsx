import React from 'react';
import { Product } from '../data/mockData';
import { TrendingUp, AlertTriangle } from 'lucide-react';

interface ProductCardProps {
  product: Product;
  onClick: (product: Product) => void;
  key?: React.Key;
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
  };

  const lowestPricePlatform = product.platforms.reduce((prev, curr) => 
    prev.price < curr.price ? prev : curr
  );

  return (
    <div 
      onClick={() => onClick(product)}
      className="group flex h-full cursor-pointer flex-col overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-zinc-200/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-zinc-200/50 hover:ring-zinc-300"
    >
      <div className="relative aspect-4/3 w-full overflow-hidden bg-zinc-50">
        <img 
          src={product.image} 
          alt={product.name} 
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          referrerPolicy="no-referrer"
        />
        {product.isTrending && (
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-rose-500/90 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-white backdrop-blur-md">
            <TrendingUp size={12} strokeWidth={3} /> Hot Deal
          </div>
        )}
      </div>
      
      <div className="flex grow flex-col p-5">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-semibold tracking-wider text-indigo-600 uppercase">{product.category}</span>
        </div>
        <h3 className="mb-4 line-clamp-2 text-sm font-medium leading-relaxed text-zinc-800 transition-colors group-hover:text-indigo-600">
          {product.name}
        </h3>
        
        <div className="mt-auto">
          <div className="mb-1.5 flex items-center justify-between">
            <p className="text-[11px] font-medium text-zinc-500">Giá tốt nhất từ <span className="font-bold text-zinc-700">{lowestPricePlatform.name}</span></p>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-lg font-bold tracking-tight text-zinc-900">{formatPrice(lowestPricePlatform.price)}</span>
            {lowestPricePlatform.originalPrice > lowestPricePlatform.price && (
              <span className="font-mono text-[11px] text-zinc-400 line-through">
                {formatPrice(lowestPricePlatform.originalPrice)}
              </span>
            )}
          </div>
          
          {product.fakeDiscountDetected && (
            <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-rose-50 px-2.5 py-2 text-[11px] font-medium text-rose-700 ring-1 ring-inset ring-rose-600/10">
              <AlertTriangle size={14} className="shrink-0" />
              <span>Cảnh báo tăng giá ảo</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
