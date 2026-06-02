import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sendAdvisorMessage } from '../advisor';
import type { AdvisorChatMessage, AdvisorChatContext } from '../advisor';

// Mock the global fetch
global.fetch = vi.fn();

describe('advisor service', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ============================================================
  // SEND ADVISOR MESSAGE
  // ============================================================
  describe('sendAdvisorMessage', () => {
    it('should send message and receive recommendations', async () => {
      const mockResponse = {
        answer: 'Here are the best options for you',
        recommendations: [
          {
            product_id: '1',
            product_name: 'iPhone 15',
            reason: 'Best value for performance',
            lowest_price: 799,
            platforms: [
              {
                platform: 'Amazon',
                price: 799,
                url: 'https://amazon.com/iphone15',
                in_stock: true
              }
            ]
          }
        ],
        sources: [
          {
            type: 'platform',
            id: '1',
            label: 'Amazon'
          }
        ]
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const message = 'What is the best phone under $1000?';
      const history: AdvisorChatMessage[] = [];
      const context: AdvisorChatContext = { search_query: 'phone' };

      const result = await sendAdvisorMessage(message, history, context);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/advisor/chat'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
      expect(result.answer).toContain('best options');
      expect(result.recommendations).toHaveLength(1);
      expect(result.recommendations[0].product_name).toBe('iPhone 15');
    });

    it('should include chat history in request', async () => {
      const mockResponse = {
        answer: 'Following up on your question',
        recommendations: [],
        sources: []
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const history: AdvisorChatMessage[] = [
        { role: 'user', content: 'Show me laptops' },
        { role: 'assistant', content: 'Here are laptops' }
      ];

      const context: AdvisorChatContext = {};

      await sendAdvisorMessage('What about gaming laptops?', history, context);

      const callArgs = (global.fetch as any).mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.history).toHaveLength(2);
      expect(body.history[0].content).toContain('laptops');
    });

    it('should include context in request', async () => {
      const mockResponse = {
        answer: 'Response',
        recommendations: [],
        sources: []
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const context: AdvisorChatContext = {
        active_tab: 'trending',
        product_id: 'prod-123',
        search_query: 'gaming'
      };

      await sendAdvisorMessage('Tell me more', [], context);

      const callArgs = (global.fetch as any).mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.context).toEqual(context);
    });

    it('should handle API errors with detail message', async () => {
      const errorResponse = {
        detail: 'Service temporarily unavailable'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(
        sendAdvisorMessage('Hello', [], {})
      ).rejects.toThrow('Service temporarily unavailable');
    });

    it('should throw default error when response has no detail', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({})
      });

      await expect(
        sendAdvisorMessage('Hello', [], {})
      ).rejects.toThrow('Không thể kết nối ProductHunter Advisor');
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(
        sendAdvisorMessage('Hello', [], {})
      ).rejects.toThrow();
    });

    it('should parse platform recommendations correctly', async () => {
      const mockResponse = {
        answer: 'Multiple options available',
        recommendations: [
          {
            product_id: '2',
            product_name: 'MacBook Pro',
            reason: 'Professional choice',
            lowest_price: 1299,
            platforms: [
              {
                platform: 'Apple Store',
                price: 1299,
                url: 'https://apple.com/macbookpro',
                in_stock: true
              },
              {
                platform: 'Best Buy',
                price: 1349,
                url: 'https://bestbuy.com/macbookpro',
                in_stock: false
              }
            ]
          }
        ],
        sources: [
          { type: 'platform', id: '1', label: 'Apple Store' },
          { type: 'platform', id: '2', label: 'Best Buy' }
        ]
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await sendAdvisorMessage('Laptops', [], {});

      expect(result.recommendations[0].platforms).toHaveLength(2);
      expect(result.sources).toHaveLength(2);
    });

    it('should handle recommendations with null prices', async () => {
      const mockResponse = {
        answer: 'Product info',
        recommendations: [
          {
            product_id: '3',
            product_name: 'Unknown Product',
            reason: 'New listing',
            lowest_price: null,
            platforms: [
              {
                platform: 'Store',
                price: null,
                url: null,
                in_stock: null
              }
            ]
          }
        ],
        sources: []
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await sendAdvisorMessage('New products', [], {});

      expect(result.recommendations[0].lowest_price).toBeNull();
      expect(result.recommendations[0].platforms[0].price).toBeNull();
    });
  });
});
