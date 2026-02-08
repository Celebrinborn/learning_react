/**
 * Tests for useAuth hook
 * Testing behavior: Hook provides auth state and functions correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { AuthProvider, useAuth } from '../hooks/useAuth';

// Mutable config ref so we can switch auth mode between tests
const mockAuthConfig = vi.hoisted(() => ({
  authMode: 'local_fake' as string,
  entraClientId: 'test-client-id',
  entraAuthority: 'https://test.ciamlogin.com/test-tenant',
  apiScope: 'api://test/access_as_user',
}));

vi.mock('../config/service.config', () => ({
  get config() {
    return { auth: mockAuthConfig };
  },
  get AUTH_MODE() {
    return mockAuthConfig.authMode;
  },
}));

// Mock auth service for local_fake mode
vi.mock('../services/auth', () => ({
  authService: {
    getCurrentUser: vi.fn(() => null),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock MSAL for entra mode
const mockMsalLogout = vi.fn();
const mockMsalAccounts = vi.hoisted(() => ({ value: [] as Array<{ username: string; name: string; localAccountId: string }> }));

vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: { logoutRedirect: mockMsalLogout },
    accounts: mockMsalAccounts.value,
    inProgress: 'none',
  }),
  useIsAuthenticated: () => mockMsalAccounts.value.length > 0,
}));

const localFakeWrapper = ({ children }: { children: ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth', () => {
  describe('in local_fake mode', () => {
    beforeEach(() => {
      vi.clearAllMocks();
      mockAuthConfig.authMode = 'local_fake';
    });

    it('provides null user when not authenticated', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
    });

    it('provides user data when authenticated', async () => {
      const mockUser = { id: '1', name: 'Test User', email: 'test@test.com' };
      const { authService } = await import('../services/auth');
      vi.mocked(authService.getCurrentUser).mockReturnValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
    });

    it('calls login service when login is invoked', async () => {
      const mockUser = { id: '1', name: 'Test User', email: 'test@test.com' };
      const { authService } = await import('../services/auth');
      vi.mocked(authService.login).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await result.current.login('username', 'password');

      expect(authService.login).toHaveBeenCalledWith('username', 'password');
    });

    it('calls logout service when logout is invoked', async () => {
      const { authService } = await import('../services/auth');
      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      result.current.logout();

      await waitFor(() => {
        expect(result.current.user).toBeNull();
      });

      expect(authService.logout).toHaveBeenCalled();
    });

    it('throws error when used outside AuthProvider', () => {
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');
    });
  });

  describe('in entra mode', () => {
    beforeEach(() => {
      vi.clearAllMocks();
      mockAuthConfig.authMode = 'entra_external_id';
      mockMsalAccounts.value = [];
    });

    it('provides null user when MSAL has no accounts', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
    });

    it('provides user from MSAL account when authenticated', async () => {
      mockMsalAccounts.value = [
        { username: 'user@example.com', name: 'Test User', localAccountId: 'abc-123' },
      ];

      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).not.toBeNull();
      expect(result.current.user?.name).toBe('Test User');
    });

    it('calls MSAL logout when logout is invoked', async () => {
      mockMsalAccounts.value = [
        { username: 'user@example.com', name: 'Test User', localAccountId: 'abc-123' },
      ];

      const { result } = renderHook(() => useAuth(), { wrapper: localFakeWrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      result.current.logout();

      expect(mockMsalLogout).toHaveBeenCalled();
    });
  });
});
