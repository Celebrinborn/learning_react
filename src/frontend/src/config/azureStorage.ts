// Re-export from service.config for backwards compatibility
import { getConfig } from './service.config';

export interface AzureStorageConfig {
  containerName: string;
}

export function getAzureStorageConfig(): AzureStorageConfig {
  const config = getConfig();
  return {
    containerName: config.storage.containerMaps,
  };
}
