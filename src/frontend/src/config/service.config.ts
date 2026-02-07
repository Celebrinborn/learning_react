/**
 * Application configuration.
 * All settings are defined here per environment.
 * Components read from getConfig() to get settings.
 */

export type Environment = 'dev' | 'test' | 'prod';
export type AuthMode = 'local_fake' | 'entra_external_id';

export interface StorageConfig {
  containerMaps: string;
  containerCharacters: string;
  containerUsers: string;
}

export interface AuthConfig {
  authMode: AuthMode;
  entraClientId: string;
  entraAuthority: string;
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
    env: 'dev',
    apiBaseUrl: 'http://localhost:8000',
    storage: {
      containerMaps: 'maps',
      containerCharacters: 'characters',
      containerUsers: 'users',
    },
    auth: {
      authMode: 'local_fake',
      entraClientId: '',
      entraAuthority: '',
      apiScope: '',
    },
  },
  test: {
    env: 'test',
    apiBaseUrl: 'https://api-test.example.com',
    storage: {
      containerMaps: 'maps-test',
      containerCharacters: 'characters-test',
      containerUsers: 'users-test',
    },
    auth: {
      authMode: 'entra_external_id',
      entraClientId: '<test-spa-client-id>',
      entraAuthority: 'https://<tenant>.ciamlogin.com/<tenant-id>',
      apiScope: 'api://<api-client-id>/access_as_user',
    },
  },
  prod: {
    env: 'prod',
    apiBaseUrl: '/api',
    storage: {
      containerMaps: 'maps',
      containerCharacters: 'characters',
      containerUsers: 'users',
    },
    auth: {
      authMode: 'entra_external_id',
      entraClientId: 'cb31ddbc-6b5b-462e-a159-0eee2cd909f6',
      entraAuthority: 'https://dndportalusers.ciamlogin.com/28a2c50b-b85c-47c4-8dd3-484dfbab055f',
      apiScope: 'api://f50fed3a-b353-4f4c-b8f5-fb26733d03e5/access_as_user',
    },
  },
};

/**
 * Get configuration for the current environment.
 * Reads from VITE_APP_ENV environment variable.
 * Defaults to 'dev' if not set.
 */
export function getConfig(): AppConfig {
  const env = (import.meta.env.VITE_APP_ENV || 'dev') as string;
  
  // Normalize environment names
  const envMap: Record<string, Environment> = {
    dev: 'dev',
    development: 'dev',
    test: 'test',
    testing: 'test',
    prod: 'prod',
    production: 'prod',
  };
  
  const normalizedEnv = envMap[env.toLowerCase()];
  if (!normalizedEnv) {
    console.warn(`Unknown environment: ${env}, defaulting to 'dev'`);
    return CONFIGS.dev;
  }
  
  return CONFIGS[normalizedEnv];
}

// Convenience exports for common config values
export const config = getConfig();
export const API_BASE_URL = config.apiBaseUrl;
export const AUTH_MODE = config.auth.authMode;
