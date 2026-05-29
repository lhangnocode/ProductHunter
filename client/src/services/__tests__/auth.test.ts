import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authService } from '../auth';

// Mock the global fetch
global.fetch = vi.fn();

describe('authService', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ============================================================
  // LOGIN
  // ============================================================
  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authService.login('test@example.com', 'password123');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
      );
      expect(result.access_token).toBe('test-access-token');
      expect(result.token_type).toBe('bearer');
    });

    it('should throw error with invalid credentials', async () => {
      const errorResponse = {
        detail: 'Invalid credentials'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(authService.login('test@example.com', 'wrongpassword'))
        .rejects
        .toThrow('Invalid credentials');
    });

    it('should send FormData with correct field names', async () => {
      const mockResponse = { access_token: 'token', token_type: 'bearer' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      await authService.login('user@example.com', 'pass');

      const callArgs = (global.fetch as any).mock.calls[0];
      const body = callArgs[1].body;
      // Body is URLSearchParams, convert to string for testing
      expect(body.toString()).toContain('username=user%40example.com');
      expect(body.toString()).toContain('password=pass');
    });
  });

  // ============================================================
  // REGISTER
  // ============================================================
  describe('register', () => {
    it('should register user successfully', async () => {
      const mockResponse = {
        id: '123',
        email: 'newuser@example.com',
        full_name: 'New User'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authService.register('newuser@example.com', 'password123', 'New User');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
      expect(result.email).toBe('newuser@example.com');
    });

    it('should throw error when email already exists', async () => {
      const errorResponse = {
        detail: 'Email already registered'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(authService.register('existing@example.com', 'password', 'User'))
        .rejects
        .toThrow('Email already registered');
    });
  });

  // ============================================================
  // FORGOT PASSWORD
  // ============================================================
  describe('forgotPassword', () => {
    it('should send password reset request successfully', async () => {
      const mockResponse = {
        message: 'Password reset email sent'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authService.forgotPassword('user@example.com');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/forgot-password'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'user@example.com' })
        })
      );
      expect(result.message).toContain('sent');
    });

    it('should throw error when email not found', async () => {
      const errorResponse = {
        detail: 'Email not registered'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(authService.forgotPassword('unknown@example.com'))
        .rejects
        .toThrow('Email not registered');
    });
  });

  // ============================================================
  // RESET PASSWORD
  // ============================================================
  describe('resetPassword', () => {
    it('should reset password successfully with valid token', async () => {
      const mockResponse = {
        message: 'Password reset successful'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await authService.resetPassword('valid-token-123', 'newpassword456');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/reset-password'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ token: 'valid-token-123', new_password: 'newpassword456' })
        })
      );
      expect(result.message).toContain('successful');
    });

    it('should throw error with invalid or expired token', async () => {
      const errorResponse = {
        detail: 'Invalid or expired token'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(authService.resetPassword('invalid-token', 'newpass'))
        .rejects
        .toThrow('Invalid or expired token');
    });
  });

  // ============================================================
  // GET ME (Current User)
  // ============================================================
  describe('getMe', () => {
    it('should fetch current user profile successfully', async () => {
      const mockUser = {
        id: '123',
        email: 'user@example.com',
        full_name: 'Test User',
        subscription_tier: 'premium'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });

      const result = await authService.getMe('valid-access-token');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({
          method: 'GET',
          headers: { 'Authorization': 'Bearer valid-access-token' }
        })
      );
      expect(result.email).toBe('user@example.com');
    });

    it('should throw error with invalid or expired token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({})
      });

      await expect(authService.getMe('invalid-token'))
        .rejects
        .toThrow('Token không hợp lệ hoặc đã hết hạn');
    });

    it('should include Bearer token in Authorization header', async () => {
      const mockUser = { id: '123', email: 'user@example.com' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });

      await authService.getMe('test-token-abc');

      const callArgs = (global.fetch as any).mock.calls[0];
      expect(callArgs[1].headers.Authorization).toBe('Bearer test-token-abc');
    });
  });
});
