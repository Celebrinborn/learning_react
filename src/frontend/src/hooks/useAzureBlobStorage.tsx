import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  localBlobStorage as blobStorage,
  BlobStorageConfig,
  UploadOptions,
  DownloadResult,
} from '../providers/localBlobStorage';

interface AzureBlobStorageContextType {
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
  uploadBlob: (options: UploadOptions) => Promise<string>;
  downloadBlob: (blobName: string) => Promise<DownloadResult>;
  deleteBlob: (blobName: string) => Promise<void>;
  listBlobs: (prefix?: string) => Promise<string[]>;
  blobExists: (blobName: string) => Promise<boolean>;
  getBlobMetadata: (blobName: string) => Promise<Record<string, string> | undefined>;
  updateBlobMetadata: (blobName: string, metadata: Record<string, string>) => Promise<void>;
}

const AzureBlobStorageContext = createContext<
  AzureBlobStorageContextType | undefined
>(undefined);

interface AzureBlobStorageProviderProps {
  children: ReactNode;
  config: BlobStorageConfig;
}

export function AzureBlobStorageProvider({
  children,
  config,
}: AzureBlobStorageProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeStorage = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Initialize the service
        blobStorage.initialize(config);

        // Verify container exists
        const exists = await blobStorage.ensureContainerExists();
        if (!exists) {
          throw new Error(`Container ${config.containerName} does not exist or is not accessible`);
        }

        setIsInitialized(true);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize Azure Blob Storage';
        setError(errorMessage);
        console.error('Azure Blob Storage initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeStorage();
  }, [config]);

  const contextValue: AzureBlobStorageContextType = {
    isInitialized,
    isLoading,
    error,
    uploadBlob: blobStorage.uploadBlob.bind(blobStorage),
    downloadBlob: blobStorage.downloadBlob.bind(blobStorage),
    deleteBlob: blobStorage.deleteBlob.bind(blobStorage),
    listBlobs: blobStorage.listBlobs.bind(blobStorage),
    blobExists: blobStorage.blobExists.bind(blobStorage),
    getBlobMetadata: blobStorage.getBlobMetadata.bind(blobStorage),
    updateBlobMetadata: blobStorage.updateBlobMetadata.bind(blobStorage),
  };

  return (
    <AzureBlobStorageContext.Provider value={contextValue}>
      {children}
    </AzureBlobStorageContext.Provider>
  );
}

export function useAzureBlobStorage() {
  const context = useContext(AzureBlobStorageContext);
  if (context === undefined) {
    throw new Error(
      'useAzureBlobStorage must be used within an AzureBlobStorageProvider'
    );
  }
  return context;
}
