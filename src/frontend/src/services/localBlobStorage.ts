// Local Blob Storage - Browser-based storage using IndexedDB
// Provides the same interface as Azure Blob Storage for local development

export interface BlobStorageConfig {
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

interface StoredBlob {
  name: string;
  data: Blob;
  contentType: string;
  metadata: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

class LocalBlobStorageService {
  private config: BlobStorageConfig | null = null;
  private dbName = 'LocalBlobStorage';
  private db: IDBDatabase | null = null;

  /**
   * Initialize the local blob storage service
   */
  initialize(config: BlobStorageConfig): void {
    this.config = config;
    this.dbName = `LocalBlobStorage_${config.containerName}`;
  }

  /**
   * Get or create the IndexedDB database
   */
  private async getDatabase(): Promise<IDBDatabase> {
    if (this.db) {
      return this.db;
    }

    return new Promise((resolve, reject) => {
      if (!this.config) {
        reject(new Error('Storage not initialized. Call initialize() first.'));
        return;
      }

      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('blobs')) {
          db.createObjectStore('blobs', { keyPath: 'name' });
        }
      };
    });
  }

  /**
   * Ensure container (database) exists and is accessible
   */
  async ensureContainerExists(): Promise<boolean> {
    try {
      await this.getDatabase();
      return true;
    } catch (error) {
      console.error('Error checking container existence:', error);
      return false;
    }
  }

  /**
   * Convert various data types to Blob
   */
  private async dataToBlob(
    data: Blob | File | ArrayBuffer | string,
    contentType: string
  ): Promise<Blob> {
    if (data instanceof Blob) {
      return data;
    } else if (data instanceof ArrayBuffer) {
      return new Blob([data], { type: contentType });
    } else if (typeof data === 'string') {
      return new Blob([data], { type: contentType });
    }
    throw new Error('Unsupported data type');
  }

  /**
   * Upload a blob to local storage
   */
  async uploadBlob(options: UploadOptions): Promise<string> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();
      const contentType = options.contentType || 'application/octet-stream';
      const blob = await this.dataToBlob(options.data, contentType);

      const storedBlob: StoredBlob = {
        name: options.blobName,
        data: blob,
        contentType,
        metadata: options.metadata || {},
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readwrite');
        const store = transaction.objectStore('blobs');
        const request = store.put(storedBlob);

        request.onsuccess = () => {
          resolve(`local://${this.config!.containerName}/${options.blobName}`);
        };

        request.onerror = () => {
          reject(new Error('Failed to upload blob'));
        };
      });
    } catch (error) {
      console.error('Error uploading blob:', error);
      throw error;
    }
  }

  /**
   * Download a blob from local storage
   */
  async downloadBlob(blobName: string): Promise<DownloadResult> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readonly');
        const store = transaction.objectStore('blobs');
        const request = store.get(blobName);

        request.onsuccess = () => {
          const storedBlob = request.result as StoredBlob | undefined;
          if (!storedBlob) {
            reject(new Error(`Blob not found: ${blobName}`));
            return;
          }

          resolve({
            data: storedBlob.data,
            metadata: storedBlob.metadata,
            contentType: storedBlob.contentType,
          });
        };

        request.onerror = () => {
          reject(new Error('Failed to download blob'));
        };
      });
    } catch (error) {
      console.error('Error downloading blob:', error);
      throw error;
    }
  }

  /**
   * Delete a blob from local storage
   */
  async deleteBlob(blobName: string): Promise<void> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readwrite');
        const store = transaction.objectStore('blobs');
        const request = store.delete(blobName);

        request.onsuccess = () => {
          resolve();
        };

        request.onerror = () => {
          reject(new Error('Failed to delete blob'));
        };
      });
    } catch (error) {
      console.error('Error deleting blob:', error);
      throw error;
    }
  }

  /**
   * List all blobs in local storage
   */
  async listBlobs(prefix?: string): Promise<string[]> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readonly');
        const store = transaction.objectStore('blobs');
        const request = store.getAllKeys();

        request.onsuccess = () => {
          let keys = request.result as string[];
          
          // Filter by prefix if provided
          if (prefix) {
            keys = keys.filter((key) => key.startsWith(prefix));
          }

          resolve(keys);
        };

        request.onerror = () => {
          reject(new Error('Failed to list blobs'));
        };
      });
    } catch (error) {
      console.error('Error listing blobs:', error);
      throw error;
    }
  }

  /**
   * Check if a blob exists
   */
  async blobExists(blobName: string): Promise<boolean> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readonly');
        const store = transaction.objectStore('blobs');
        const request = store.get(blobName);

        request.onsuccess = () => {
          resolve(request.result !== undefined);
        };

        request.onerror = () => {
          reject(new Error('Failed to check blob existence'));
        };
      });
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
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readonly');
        const store = transaction.objectStore('blobs');
        const request = store.get(blobName);

        request.onsuccess = () => {
          const storedBlob = request.result as StoredBlob | undefined;
          if (!storedBlob) {
            reject(new Error(`Blob not found: ${blobName}`));
            return;
          }
          resolve(storedBlob.metadata);
        };

        request.onerror = () => {
          reject(new Error('Failed to get blob metadata'));
        };
      });
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
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readwrite');
        const store = transaction.objectStore('blobs');
        const getRequest = store.get(blobName);

        getRequest.onsuccess = () => {
          const storedBlob = getRequest.result as StoredBlob | undefined;
          if (!storedBlob) {
            reject(new Error(`Blob not found: ${blobName}`));
            return;
          }

          storedBlob.metadata = metadata;
          storedBlob.updatedAt = new Date().toISOString();

          const putRequest = store.put(storedBlob);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(new Error('Failed to update metadata'));
        };

        getRequest.onerror = () => {
          reject(new Error('Failed to get blob for metadata update'));
        };
      });
    } catch (error) {
      console.error('Error updating blob metadata:', error);
      throw error;
    }
  }

  /**
   * Clear all blobs (useful for testing/reset)
   */
  async clearAll(): Promise<void> {
    if (!this.config) {
      throw new Error('Storage not initialized. Call initialize() first.');
    }

    try {
      const db = await this.getDatabase();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['blobs'], 'readwrite');
        const store = transaction.objectStore('blobs');
        const request = store.clear();

        request.onsuccess = () => {
          resolve();
        };

        request.onerror = () => {
          reject(new Error('Failed to clear storage'));
        };
      });
    } catch (error) {
      console.error('Error clearing storage:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const localBlobStorage = new LocalBlobStorageService();
