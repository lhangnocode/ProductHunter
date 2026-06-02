// client/src/components/__tests__/ProductCard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../utils/test-utils';
import { ProductCard } from '../ProductCard';
import { LanguageProvider } from '../../context/LanguageContext';
import React from 'react';

const mockProduct = {
  id: "test-123",
  normalized_name: "Test Product iPhone",
  main_image_url: "https://example.com/test.jpg",
  lowest_price: 10000000,
  platforms: [{ platform_id: 9, current_price: 10000000 }]
};

// Wrapper component để test với locale cụ thể
const renderWithLanguage = (component: React.ReactElement, language: 'vi' | 'en' = 'vi') => {
  // Mocking localStorage
  const store: { [key: string]: string } = {};
  const mockLocalStorage = {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach(key => delete store[key]); }
  };
  
  Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
  mockLocalStorage.setItem('language', language);
  
  return render(
    <LanguageProvider>
      {component}
    </LanguageProvider>
  );
};

describe('ProductCard Component', () => {
    it('renders product information correctly in Vietnamese', () => {
        renderWithLanguage(
            <ProductCard 
                product={mockProduct} 
                onClick={vi.fn()} 
                isWishlisted={false} 
            />,
            'vi'
        );
        
        expect(screen.getByText(/Test Product/i)).toBeInTheDocument();
        // Với locale vi-VN, Intl.NumberFormat format như: 10 000 000 (với khoảng trắng)
        expect(screen.getByText(/10[\s.′,]000[\s.′,]000/)).toBeInTheDocument();
    });

    it('triggers onClick handler when card is clicked', () => {
        const handleClick = vi.fn();
        renderWithLanguage(
            <ProductCard 
                product={mockProduct} 
                onClick={handleClick}
            />,
            'vi'
        );
        
        const card = screen.getByText(/Test Product/i).closest('div');
        fireEvent.click(card!);
        expect(handleClick).toHaveBeenCalledWith(mockProduct, "test-123");
    });
});
