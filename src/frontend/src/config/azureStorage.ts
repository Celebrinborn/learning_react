// Configuration for Blob Storage
// Currently using local storage for development

export interface AzureStorageConfig {
  containerName: string;
}

export function getAzureStorageConfig(): AzureStorageConfig {
  // For local development, just use a simple container name
  // No Azure credentials needed
  return {
    containerName: 'dnd-local-storage',
  };
}
