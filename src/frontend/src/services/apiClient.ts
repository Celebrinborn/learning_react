/**
 * Authenticated API client.
 * In entra mode, acquires a token and attaches it as a Bearer header.
 * In local_fake mode, makes plain requests.
 */
import { config } from '../config/service.config';
import { getMsalInstance } from '../auth/msalInstance';

async function getAccessToken(): Promise<string | null> {
  if (config.auth.authMode !== 'entra_external_id') {
    return null;
  }

  const instance = getMsalInstance();
  const accounts = instance.getAllAccounts();
  if (accounts.length === 0) {
    return null;
  }

  const result = await instance.acquireTokenSilent({
    scopes: [config.auth.apiScope],
    account: accounts[0],
  });
  return result.accessToken;
}

export const apiClient = {
  async fetch(path: string, options?: RequestInit): Promise<Response> {
    const url = `${config.apiBaseUrl}${path}`;
    const headers = new Headers(options?.headers);

    const token = await getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return globalThis.fetch(url, { ...options, headers });
  },
};
