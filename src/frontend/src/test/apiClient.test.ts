/**
 * Tests for apiClient
 * Testing behavior: Requests include auth tokens when in entra mode
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mutable config ref
const mockAuthConfig = vi.hoisted(() => ({
  authMode: 'local_fake' as string,
  entraClientId: 'test-client-id',
  entraAuthority: 'https://test.ciamlogin.com/test-tenant',
  apiScope: 'api://test/access_as_user',
}));

vi.mock('../config/service.config', () => ({
  get config() {
    return {
      apiBaseUrl: 'http://localhost:8000',
      auth: mockAuthConfig,
    };
  },
  get API_BASE_URL() {
    return 'http://localhost:8000';
  },
}));

// Mock shared MSAL instance
const mockAcquireTokenSilent = vi.fn();
const mockGetAllAccounts = vi.fn().mockReturnValue([{ localAccountId: '123' }]);
vi.mock('../auth/msalInstance', () => ({
  getMsalInstance: () => ({
    acquireTokenSilent: mockAcquireTokenSilent,
    getAllAccounts: mockGetAllAccounts,
  }),
}));

import { apiClient } from '../services/apiClient';

describe('apiClient', () => {
  const originalFetch = globalThis.fetch;
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });
    globalThis.fetch = mockFetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.clearAllMocks();
  });

  describe('in local_fake mode', () => {
    beforeEach(() => {
      mockAuthConfig.authMode = 'local_fake';
    });

    it('makes requests without Authorization header', async () => {
      await apiClient.fetch('/api/map-locations');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/map-locations',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.any(String),
          }),
        }),
      );
    });

    it('passes through request options', async () => {
      await apiClient.fetch('/api/map-locations', {
        method: 'POST',
        body: JSON.stringify({ name: 'test' }),
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/map-locations',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'test' }),
        }),
      );
    });
  });

  describe('in entra mode', () => {
    beforeEach(() => {
      mockAuthConfig.authMode = 'entra_external_id';
      mockAcquireTokenSilent.mockResolvedValue({ accessToken: 'test-token-123' });
    });

    it('attaches Bearer token to requests', async () => {
      await apiClient.fetch('/api/map-locations');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers.get('Authorization')).toBe('Bearer test-token-123');
    });

    it('includes Content-Type when provided', async () => {
      await apiClient.fetch('/api/map-locations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test' }),
      });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers.get('Authorization')).toBe('Bearer test-token-123');
      expect(options.headers.get('Content-Type')).toBe('application/json');
    });
  });
});
