import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchProducts } from '../price_record_api';

// Mock the global fetch
global.fetch = vi.fn();

describe('price_record_api', () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    it('searchProducts resolves correctly when API returns success', async () => {
        const mockData = {
            data: [
                { id: "1", normalized_name: "Mock Item" }
            ],
            total_pages: 1,
            total_results: 1
        };

        // Mock the fetch response
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData
        });

        const result = await searchProducts("mock query");
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/products/search?q=mock%20query'));
        expect(result).toHaveLength(1);
        expect(result[0].normalized_name).toBe("Mock Item");
    });

    it('searchProducts handles 422 error by logging and returning empty array', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        
        (global.fetch as any).mockResolvedValueOnce({
            ok: false,
            status: 422,
            json: async () => ({ detail: "Invalid query" })
        });

        const result = await searchProducts("a");
        expect(result).toEqual([]);
        expect(consoleSpy).toHaveBeenCalled();
        
        consoleSpy.mockRestore();
    });
});
