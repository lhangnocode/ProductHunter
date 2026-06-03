import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchProducts, searchPlatformProducts } from '../price_record_api';

// Mock the global fetch
global.fetch = vi.fn();

describe('price_record_api', () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    // ============================================================
    // SEARCH PRODUCTS
    // ============================================================
    describe('searchProducts', () => {
        it('should search products successfully with query string', async () => {
            const mockData = {
                data: [
                    { id: "1", normalized_name: "Mock Item" }
                ],
                total_pages: 1,
                total_results: 1
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchProducts("mock query");
            
            expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/products/search?q=mock%20query'));
            expect(result.items).toHaveLength(1);
            expect(result.items[0].normalized_name).toBe("Mock Item");
            expect(result.page).toBe(1);
        });

        it('should support pagination parameters', async () => {
            const mockData = {
                data: [{ id: "1", normalized_name: "Item" }],
                page: 2,
                size: 10,
                total_elements: 100,
                total_pages: 10
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchProducts("test", 2, 10);

            const url = (global.fetch as any).mock.calls[0][0];
            expect(url).toContain('page=2');
            expect(url).toContain('limit=10');
            expect(result.page).toBe(2);
            expect(result.size).toBe(10);
            expect(result.total_pages).toBe(10);
        });

        it('should handle different response envelope formats', async () => {
            const mockData = {
                items: [
                    { id: "1", name: "Item 1" },
                    { id: "2", name: "Item 2" }
                ],
                page: 1,
                size: 24,
                total_elements: 2,
                total_pages: 1
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchProducts("query");

            expect(result.items).toHaveLength(2);
            expect(result.total_elements).toBe(2);
        });

        it('should parse array response directly', async () => {
            const mockData = [
                { id: "1", name: "Item 1" },
                { id: "2", name: "Item 2" }
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchProducts("query");

            expect(result.items).toHaveLength(2);
        });

        it('should handle error response with 422 status', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
            
            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                status: 422,
                json: async () => ({ detail: "Invalid query" })
            });

            const result = await searchProducts("a");
            
            expect(result.items).toEqual([]);
            expect(result.total_elements).toBe(0);
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });

        it('should handle 404 not found error', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                status: 404,
                json: async () => ({ detail: "Not found" })
            });

            const result = await searchProducts("nonexistent");

            expect(result.items).toEqual([]);
            expect(consoleSpy).toHaveBeenCalled();

            consoleSpy.mockRestore();
        });

        it('should handle network errors gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

            (global.fetch as any).mockRejectedValueOnce(
                new Error('Network error')
            );

            const result = await searchProducts("query");

            expect(result.items).toEqual([]);
            expect(consoleSpy).toHaveBeenCalled();

            consoleSpy.mockRestore();
        });

        it('should use default pagination values', async () => {
            const mockData = { data: [] };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchProducts("query");

            expect(result.page).toBe(1);
            expect(result.size).toBe(24);
        });

        it('should return default pagination on missing values', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ items: [] })
            });

            const result = await searchProducts("query");

            expect(result.total_elements).toBe(0);
            expect(result.total_pages).toBe(0);
        });

        it('should properly encode query strings with special characters', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ data: [] })
            });

            await searchProducts("iphone & android/google");

            const url = (global.fetch as any).mock.calls[0][0];
            // URL should be properly encoded
            expect(url).toContain('%20'); // space
            expect(url).toContain('%26'); // &
            expect(url).toContain('%2F'); // /
        });
    });

    // ============================================================
    // SEARCH PLATFORM PRODUCTS
    // ============================================================
    describe('searchPlatformProducts', () => {
        it('should search platform products by product id', async () => {
            const mockData = [
                {
                    id: '1',
                    product_id: 'prod-1',
                    platform_id: 1,
                    raw_name: 'iPhone 15',
                    current_price: 999,
                    original_price: 1099,
                    url: 'https://example.com/iphone',
                    in_stock: true
                }
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchPlatformProducts('prod-1');

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/platform_products/platform-products/by-product-id')
            );
            expect(result).toHaveLength(1);
            expect(result[0].raw_name).toBe('iPhone 15');
        });

        it('should normalize numeric fields to numbers', async () => {
            const mockData = [
                {
                    id: '1',
                    product_id: 'prod-1',
                    current_price: '999.99',
                    original_price: '1099.99',
                    platform_id: 1,
                    raw_name: 'Product',
                    url: 'https://example.com',
                    in_stock: true
                }
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchPlatformProducts('prod-1');

            expect(typeof result[0].current_price).toBe('number');
            expect(result[0].current_price).toBe(999.99);
            expect(result[0].original_price).toBe(1099.99);
        });

        it('should handle null prices', async () => {
            const mockData = [
                {
                    id: '1',
                    product_id: 'prod-1',
                    platform_id: 1,
                    raw_name: 'Product',
                    current_price: null,
                    original_price: null,
                    url: 'https://example.com',
                    in_stock: true
                }
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchPlatformProducts('prod-1');

            expect(result[0].current_price).toBeNull();
            expect(result[0].original_price).toBeNull();
        });

        it('should handle error response', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Search failed' })
            });

            await expect(searchPlatformProducts('prod-1'))
                .rejects
                .toThrow('Search failed');
        });

        it('should handle empty results array', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => []
            });

            const result = await searchPlatformProducts('nonexistent-prod');

            expect(result).toEqual([]);
        });

        it('should handle response wrapped in data property', async () => {
            const mockData = {
                data: [
                    {
                        id: '1',
                        product_id: 'prod-1',
                        platform_id: 1,
                        raw_name: 'Product',
                        current_price: 100,
                        original_price: 150,
                        url: 'https://example.com',
                        in_stock: true
                    }
                ]
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockData
            });

            const result = await searchPlatformProducts('prod-1');

            expect(result).toHaveLength(1);
            expect(result[0].product_id).toBe('prod-1');
        });

        it('should encode product id in URL', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => []
            });

            await searchPlatformProducts('prod-1/special');

            const url = (global.fetch as any).mock.calls[0][0];
            // URL should be properly encoded
            expect(url).toContain('%2F'); // forward slash should be encoded
        });
    });
});
