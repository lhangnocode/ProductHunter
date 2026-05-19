import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../utils/test-utils';
import { ProductCard } from '../ProductCard';
import React from 'react';

const mockProduct = {
  id: "test-123",
  normalized_name: "Test Product iPhone",
  main_image_url: "https://example.com/test.jpg",
  lowest_price: 10000000,
  platforms: [
    {
       platform_id: 1,
       current_price: 10000000
    }
  ]
};

describe('ProductCard Component', () => {
    it('renders product information correctly', () => {
        render(
            <ProductCard 
                product={mockProduct} 
                onClick={vi.fn()} 
                isWishlisted={false} 
            />
        );
        
        expect(screen.getByText(/Test Product/i)).toBeInTheDocument();
        // Since we format price as 10.000.000 ₫, we look for 10.000.000
        expect(screen.getByText(/10\.000\.000|10,000,000/)).toBeInTheDocument();
    });

    it('triggers onClick handler when card is clicked', () => {
        const handleClick = vi.fn();
        render(
            <ProductCard 
                product={mockProduct} 
                onClick={handleClick}
            />
        );
        
        const card = screen.getByText(/Test Product/i).closest('div');
        fireEvent.click(card!);
        expect(handleClick).toHaveBeenCalledWith(mockProduct, "test-123");
    });
});
