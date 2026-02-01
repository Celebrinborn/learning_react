import { BlobServiceClient, ContainerClient } from '@azure/storage-blob';

export interface BlobStorageConfig {
  connectionString?: string;
  accountName?: string;
  sasToken?: string;
  containerName: string;
}

export interface UploadOptions {
  blobName: string;
  data: Blob | File | ArrayBuffer | string;
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface DownloadResult {
  data: Blob;
  metadata?: Record<string, string>;
  contentType?: string;
}

class AzureBlobStorageService {
  private containerClient: ContainerClient | null = null;
  private config: BlobStorageConfig | null = null;

  /**
   * Initialize the blob storage service with configuration
   * You can use either:
   * 1. Connection string (for development)
   * 2. Account name + SAS token (recommended for production)
   */
  initialize(config: BlobStorageConfig): void {
    this.config = config;

    try {
      if (config.connectionString) {
        // Initialize with connection string
        const blobServiceClient = BlobServiceClient.fromConnectionString(
          config.connectionString
        );
        this.containerClient = blobServiceClient.getContainerClient(
          config.containerName
        );
      } else if (config.accountName && config.sasToken) {
        // Initialize with account name and SAS token
        const blobServiceClient = new BlobServiceClient(
          `https://${config.accountName}.blob.core.windows.net?${config.sasToken}`
        );
        this.containerClient = blobServiceClient.getContainerClient(
          config.containerName
        );
      } else {
        throw new Error(
          'Must provide either connectionString or accountName with sasToken'
        );
      }
    } catch (error) {
      console.error('Failed to initialize Azure Blob Storage:', error);
      throw error;
    }
  }

  /**
   * Ensure container exists and is accessible
   */
  async ensureContainerExists(): Promise<boolean> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const exists = await this.containerClient.exists();
      if (!exists) {
        console.warn(`Container ${this.config?.containerName} does not exist`);
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error checking container existence:', error);
      return false;
    }
  }

  /**
   * Upload a blob to Azure Storage
   */
  async uploadBlob(options: UploadOptions): Promise<string> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(
        options.blobName
      );

      const uploadOptions = {
        blobHTTPHeaders: {
          blobContentType: options.contentType || 'application/octet-stream',
        },
        metadata: options.metadata,
      };

      if (options.data instanceof Blob || options.data instanceof File) {
        await blockBlobClient.uploadData(options.data, uploadOptions);
      } else if (typeof options.data === 'string') {
        await blockBlobClient.upload(
          options.data,
          options.data.length,
          uploadOptions
        );
      } else if (options.data instanceof ArrayBuffer) {
        await blockBlobClient.uploadData(options.data, uploadOptions);
      }

      return blockBlobClient.url;
    } catch (error) {
      console.error('Error uploading blob:', error);
      throw error;
    }
  }

  /**
   * Download a blob from Azure Storage
   */
  async downloadBlob(blobName: string): Promise<DownloadResult> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(blobName);
      const downloadResponse = await blockBlobClient.download(0);

      if (!downloadResponse.blobBody) {
        throw new Error('No blob body returned');
      }

      const data = await downloadResponse.blobBody;

      return {
        data,
        metadata: downloadResponse.metadata,
        contentType: downloadResponse.contentType,
      };
    } catch (error) {
      console.error('Error downloading blob:', error);
      throw error;
    }
  }

  /**
   * Delete a blob from Azure Storage
   */
  async deleteBlob(blobName: string): Promise<void> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(blobName);
      await blockBlobClient.delete();
    } catch (error) {
      console.error('Error deleting blob:', error);
      throw error;
    }
  }

  /**
   * List all blobs in the container
   */
  async listBlobs(prefix?: string): Promise<string[]> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blobNames: string[] = [];
      const iterator = this.containerClient.listBlobsFlat({ prefix });

      for await (const blob of iterator) {
        blobNames.push(blob.name);
      }

      return blobNames;
    } catch (error) {
      console.error('Error listing blobs:', error);
      throw error;
    }
  }

  /**
   * Check if a blob exists
   */
  async blobExists(blobName: string): Promise<boolean> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(blobName);
      return await blockBlobClient.exists();
    } catch (error) {
      console.error('Error checking blob existence:', error);
      return false;
    }
  }

  /**
   * Get blob metadata
   */
  async getBlobMetadata(
    blobName: string
  ): Promise<Record<string, string> | undefined> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(blobName);
      const properties = await blockBlobClient.getProperties();
      return properties.metadata;
    } catch (error) {
      console.error('Error getting blob metadata:', error);
      throw error;
    }
  }

  /**
   * Update blob metadata
   */
  async updateBlobMetadata(
    blobName: string,
    metadata: Record<string, string>
  ): Promise<void> {
    if (!this.containerClient) {
      throw new Error('Blob storage not initialized. Call initialize() first.');
    }

    try {
      const blockBlobClient = this.containerClient.getBlockBlobClient(blobName);
      await blockBlobClient.setMetadata(metadata);
    } catch (error) {
      console.error('Error updating blob metadata:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const azureBlobStorage = new AzureBlobStorageService();
