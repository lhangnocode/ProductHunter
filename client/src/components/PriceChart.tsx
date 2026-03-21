import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { PriceHistoryPoint } from '../data/mockData';

interface PriceChartProps {
  data: PriceHistoryPoint[];
}

export function PriceChart({ data }: PriceChartProps) {
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
  };

  return (
    <div className="h-75 w-full mt-6">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e4e4e7" />
          <XAxis 
            dataKey="date" 
            stroke="#a1a1aa" 
            fontSize={12} 
            tickLine={false} 
            axisLine={false} 
            dy={10}
          />
          <YAxis 
            stroke="#a1a1aa" 
            fontSize={12} 
            tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
            tickLine={false} 
            axisLine={false}
            width={45}
            dx={-10}
            fontFamily="JetBrains Mono"
          />
          <Tooltip 
            formatter={(value) => value !== undefined ? [formatPrice(value as number), 'Giá'] : []}
            labelStyle={{ color: '#52525b', fontWeight: 500, marginBottom: '4px' }}
            contentStyle={{ 
              borderRadius: '12px', 
              border: '1px solid #e4e4e7', 
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
              padding: '12px 16px',
              fontFamily: 'Inter, sans-serif'
            }}
            itemStyle={{
              color: '#09090b',
              fontWeight: 700,
              fontFamily: 'JetBrains Mono'
            }}
          />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke="#10b981" 
            strokeWidth={2.5}
            fillOpacity={1} 
            fill="url(#colorPrice)"
            activeDot={{ r: 6, strokeWidth: 0, fill: '#10b981' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}