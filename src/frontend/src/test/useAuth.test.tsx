/**
 * Tests for useAuth hook
 * Testing behavior: Hook provides auth state and functions correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { AuthProvider, useAuth } from '../hooks/useAuth';

// Mock the auth service
vi.mock('../providers/auth', () => ({
  authService: {
    getCurrentUser: vi.fn(() => null),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

const wrapper = ({ children }: { children: ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides null user when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('provides user data when authenticated', async () => {
    const mockUser = { id: '1', name: 'Test User', email: 'test@test.com' };
    const { authService } = await import('../providers/auth');
    vi.mocked(authService.getCurrentUser).mockReturnValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it('calls login service when login is invoked', async () => {
    const mockUser = { id: '1', name: 'Test User', email: 'test@test.com' };
    const { authService } = await import('../providers/auth');
    vi.mocked(authService.login).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.login('username', 'password');

    expect(authService.login).toHaveBeenCalledWith('username', 'password');
  });

  it('calls logout service when logout is invoked', async () => {
    const { authService } = await import('../providers/auth');
    const { result } = renderHook(() => useAuth(), { wrapper });

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
