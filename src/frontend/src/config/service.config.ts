/**
 * Service-level configuration.
 * Defines how the frontend communicates with backend services.
 */

import { config } from "./app.config";

// Re-export app-level config for consumers that import from service.config
export { config, getConfig, AUTH_MODE } from "./app.config";
export type { AppConfig, AuthConfig, AuthMode, Environment } from "./app.config";

export const API_BASE_URL = config.apiBaseUrl;

export const DEFAULT_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
};

export const REQUEST_TIMEOUT_MS = 10_000;

/**
 * Helper to build full API URLs.
 */
export function buildApiUrl(path: string): string {
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }
  return `${API_BASE_URL}${path}`;
}
