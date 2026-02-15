/**
 * Tests for useAuth hook
 * Testing behavior: Hook provides auth state and functions via MSAL
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { AuthProvider, useAuth } from '../hooks/useAuth';

// Mock MSAL
const mockMsalLogout = vi.fn();
const mockMsalAccounts = vi.hoisted(() => ({ value: [] as Array<{ username: string; name: string; localAccountId: string }> }));
const mockMsalInProgress = vi.hoisted(() => ({ value: 'none' as string }));

vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: { logoutRedirect: mockMsalLogout, getActiveAccount: () => null },
    accounts: mockMsalAccounts.value,
    inProgress: mockMsalInProgress.value,
  }),
  MsalProvider: ({ children }: { children: ReactNode }) => children,
}));

vi.mock('../auth/msalInstance', () => ({
  getMsalInstance: () => ({}),
}));

const wrapper = ({ children }: { children: ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMsalAccounts.value = [];
    mockMsalInProgress.value = 'none';
  });

  it('throws error when used outside AuthProvider', () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');
  });

  it('provides null user when MSAL has no accounts', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('provides user from MSAL account when authenticated', async () => {
    mockMsalAccounts.value = [
      { username: 'user@example.com', name: 'Test User', localAccountId: 'abc-123' },
    ];

    const { result } = renderHook(() => useAuth(), { wrapper });

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

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    result.current.logout();

    expect(mockMsalLogout).toHaveBeenCalled();
  });

  it('isLoading is true while MSAL redirect is in progress', () => {
    mockMsalInProgress.value = 'login';

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
  });
});
