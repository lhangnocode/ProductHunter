import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { PriceHistoryPoint } from '../data/mockData';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

interface PriceChartProps {
  data: PriceHistoryPoint[];
}

export function PriceChart({ data }: PriceChartProps) {
  const { language, t } = useLanguage();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

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

  return (
    <div className="h-[300px] w-full mt-6">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff4d00" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#ff4d00" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" vertical={false} stroke={isDark ? '#334155' : '#e2e8f0'} />
          <XAxis 
            dataKey="date" 
            stroke={isDark ? '#64748b' : '#94a3b8'} 
            fontSize={10} 
            tickLine={false} 
            axisLine={false} 
            dy={10}
            fontFamily="Inter"
            fontWeight={700}
            tickFormatter={(value) => value.toUpperCase()}
          />
          <YAxis 
            stroke={isDark ? '#64748b' : '#94a3b8'} 
            fontSize={10} 
            tickFormatter={(value) => language === 'vi' ? `${(value / 1000000).toFixed(1)}M` : `$${(value / 25000).toFixed(0)}`}
            tickLine={false} 
            axisLine={false}
            width={45}
            dx={-10}
            fontFamily="JetBrains Mono"
            fontWeight={700}
          />
          <Tooltip 
            formatter={(value) => value !== undefined && value !== null ? [formatPrice(value as number), language === 'vi' ? 'Giá' : 'Price'] : ['-', language === 'vi' ? 'Giá' : 'Price']}
            labelStyle={{ color: isDark ? '#94a3b8' : '#475569', fontWeight: 900, marginBottom: '4px', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.15em' }}
            contentStyle={{ 
              borderRadius: '16px', 
              backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              border: `1px solid ${isDark ? 'rgba(51, 65, 85, 0.6)' : 'rgba(226, 232, 240, 0.6)'}`, 
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
              padding: '12px 16px',
              backdropFilter: 'blur(16px)',
              fontFamily: 'Inter, sans-serif'
            }}
            itemStyle={{
              color: '#ff4d00',
              fontWeight: 900,
              fontSize: '16px',
              fontFamily: 'JetBrains Mono',
              letterSpacing: '-0.05em'
            }}
          />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke="#ff4d00" 
            strokeWidth={3}
            fillOpacity={1} 
            fill="url(#colorPrice)"
            activeDot={{ r: 6, strokeWidth: 3, stroke: isDark ? '#0f172a' : '#fff', fill: '#ff4d00' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}