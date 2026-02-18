/**
 * Application configuration.
 * All environment-specific settings live here.
 * This file contains *data*, not protocol logic.
 */

export type Environment = "dev" | "test" | "prod";
export type AuthMode = "entra_external_id";

export interface StorageConfig {
  containerMaps: string;
  containerCharacters: string;
  containerUsers: string;
}

export interface AuthConfig {
  authMode: AuthMode;

  // Entra / CIAM identifiers (non-secret)
  entraClientId: string;

  // CIAM authority parts (kept separate for clarity)
  entraAuthorityHost: string; // e.g. dndportal.ciamlogin.com
  entraTenantId: string;      // e.g. 28a2c50b-...

  // Redirect back to SPA
  entraRedirectUri: string;

  // OAuth scope exposed by the API
  apiScope: string;
}

export interface AppConfig {
  env: Environment;
  apiBaseUrl: string;
  storage: StorageConfig;
  auth: AuthConfig;
}

const CONFIGS: Record<Environment, AppConfig> = {
  dev: {
    env: "dev",
    apiBaseUrl: "http://localhost:8000",
    storage: {
      containerMaps: "maps",
      containerCharacters: "characters",
      containerUsers: "users",
    },
    auth: {
      authMode: "entra_external_id",
      entraClientId: "cb31ddbc-6b5b-462e-a159-0eee2cd909f6",
      entraAuthorityHost: "dndportal.ciamlogin.com",
      entraTenantId: "28a2c50b-b85c-47c4-8dd3-484dfbab055f",
      entraRedirectUri: "http://localhost:5173/",
      apiScope: "api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5/access_as_user",
    },
  },

  test: {
    env: "test",
    apiBaseUrl: "https://api-test.example.com",
    storage: {
      containerMaps: "maps-test",
      containerCharacters: "characters-test",
      containerUsers: "users-test",
    },
    auth: {
      authMode: "entra_external_id",
      entraClientId: "<test-spa-client-id>",
      entraAuthorityHost: "dndportal.ciamlogin.com",
      entraTenantId: "28a2c50b-b85c-47c4-8dd3-484dfbab055f",
      entraRedirectUri: "https://test.example.com/",
      apiScope: "api://<api-client-id>/access_as_user",
    },
  },

  prod: {
    env: "prod",
    apiBaseUrl: "",
    storage: {
      containerMaps: "maps",
      containerCharacters: "characters",
      containerUsers: "users",
    },
    auth: {
      authMode: "entra_external_id",
      entraClientId: "cb31ddbc-6b5b-462e-a159-0eee2cd909f6",
      entraAuthorityHost: "dndportal.ciamlogin.com",
      entraTenantId: "28a2c50b-b85c-47c4-8dd3-484dfbab055f",
      entraRedirectUri: window.location.origin,
      apiScope: "api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5/access_as_user",
    },
  },
};

/**
 * Resolve configuration for the current environment.
 * Uses VITE_APP_ENV, defaults to 'dev'.
 */
export function getConfig(): AppConfig {
  const rawEnv = (import.meta.env.VITE_APP_ENV || "dev").toLowerCase();

  const envMap: Record<string, Environment> = {
    dev: "dev",
    development: "dev",
    test: "test",
    testing: "test",
    prod: "prod",
    production: "prod",
  };

  const env = envMap[rawEnv];
  if (!env) {
    console.warn(`Unknown environment '${rawEnv}', defaulting to 'dev'`);
    return CONFIGS.dev;
  }

  return CONFIGS[env];
}

// Convenience exports
export const config = getConfig();
export const API_BASE_URL = config.apiBaseUrl;
export const AUTH_MODE = config.auth.authMode;
