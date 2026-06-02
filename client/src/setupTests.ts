import '@testing-library/jest-dom';
import { vi } from 'vitest';

const localStorageMock = (function () {
  let store: Record<string, string> = {};
  return {
    getItem(key: string) {
      return store[key] || null;
    },
    setItem(key: string, value: string) {
      store[key] = value.toString();
    },
    removeItem(key: string) {
      delete store[key];
    },
    clear() {
      store = {};
    }
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Giả lập (Mock) Window.matchMedia cho các component có dùng Responsive CSS/JS
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Giả lập biến Môi trường
vi.stubGlobal('import.meta', {
  env: {
    VITE_API_URL: 'http://localhost:8000/api/v1',
  }
});
