/**
 * Authenticated API client.
 * Acquires a token via MSAL and attaches it as a Bearer header.
 */
import { config } from '../config/service.config';
import { getMsalInstance } from '../auth/msalInstance';

async function getAccessToken(): Promise<string | null> {
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
