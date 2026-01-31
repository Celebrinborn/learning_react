# Azure Blob Storage Provider Setup

## Overview
This project includes an Azure Blob Storage provider for uploading, downloading, and managing files in Azure Storage.

## Installation

Install the required Azure Storage SDK:

```bash
npm install @azure/storage-blob
```

## Configuration

### 1. Create .env file

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 2. Configure Azure Storage

You have two options:

**Option A: Connection String (Development)**
```env
VITE_AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
VITE_AZURE_STORAGE_CONTAINER_NAME=your-container
```

**Option B: Account Name + SAS Token (Production)**
```env
VITE_AZURE_STORAGE_ACCOUNT_NAME=youraccount
VITE_AZURE_STORAGE_SAS_TOKEN=?sv=2021-06-08&ss=b&srt=sco&sp=rwdlac...
VITE_AZURE_STORAGE_CONTAINER_NAME=your-container
```

### 3. Get Your Azure Credentials

#### Connection String:
1. Go to Azure Portal
2. Navigate to your Storage Account
3. Click "Access keys" in the left sidebar
4. Copy the "Connection string"

#### SAS Token:
1. Go to Azure Portal
2. Navigate to your Storage Account
3. Click "Shared access signature" in the left sidebar
4. Configure permissions and expiry
5. Click "Generate SAS and connection string"
6. Copy the "SAS token"

## Usage

### Wrap Your App with the Provider

```tsx
import { AzureBlobStorageProvider } from './hooks/useAzureBlobStorage';
import { getAzureStorageConfig } from './config/azureStorage';

function App() {
  const config = getAzureStorageConfig();
  
  return (
    <AzureBlobStorageProvider config={config}>
      <YourApp />
    </AzureBlobStorageProvider>
  );
}
```

### Use the Hook in Components

```tsx
import { useAzureBlobStorage } from '../hooks/useAzureBlobStorage';

function MyComponent() {
  const { 
    uploadBlob, 
    downloadBlob, 
    listBlobs,
    isInitialized,
    isLoading,
    error 
  } = useAzureBlobStorage();

  // Check if ready
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!isInitialized) return <div>Not initialized</div>;

  // Upload a file
  const handleUpload = async (file: File) => {
    try {
      const url = await uploadBlob({
        blobName: `uploads/${file.name}`,
        data: file,
        contentType: file.type,
        metadata: {
          uploadedBy: 'user123',
          timestamp: new Date().toISOString(),
        }
      });
      console.log('Uploaded to:', url);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // Download a file
  const handleDownload = async (blobName: string) => {
    try {
      const result = await downloadBlob(blobName);
      // Create download link
      const url = URL.createObjectURL(result.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = blobName;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // List files
  const handleListFiles = async () => {
    try {
      const blobs = await listBlobs('uploads/');
      console.log('Files:', blobs);
    } catch (error) {
      console.error('List failed:', error);
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => {
        if (e.target.files?.[0]) {
          handleUpload(e.target.files[0]);
        }
      }} />
      <button onClick={handleListFiles}>List Files</button>
    </div>
  );
}
```

## API Reference

### Provider Props
- `config`: Azure Storage configuration object
- `children`: React children

### Hook Return Values

#### State
- `isInitialized`: Whether storage is ready to use
- `isLoading`: Whether initialization is in progress
- `error`: Error message if initialization failed

#### Methods

**uploadBlob(options)**
```tsx
await uploadBlob({
  blobName: 'path/to/file.txt',
  data: file, // File, Blob, ArrayBuffer, or string
  contentType: 'text/plain', // optional
  metadata: { key: 'value' } // optional
});
```

**downloadBlob(blobName)**
```tsx
const result = await downloadBlob('path/to/file.txt');
// result.data: Blob
// result.metadata: Record<string, string>
// result.contentType: string
```

**deleteBlob(blobName)**
```tsx
await deleteBlob('path/to/file.txt');
```

**listBlobs(prefix?)**
```tsx
const blobs = await listBlobs('uploads/'); // Returns string[]
```

**blobExists(blobName)**
```tsx
const exists = await blobExists('path/to/file.txt'); // Returns boolean
```

**getBlobMetadata(blobName)**
```tsx
const metadata = await getBlobMetadata('path/to/file.txt');
```

**updateBlobMetadata(blobName, metadata)**
```tsx
await updateBlobMetadata('path/to/file.txt', { key: 'value' });
```

## Security Best Practices

1. **Never commit .env files** - Add `.env` to `.gitignore`
2. **Use SAS tokens in production** - They can be scoped and have expiry
3. **Limit SAS token permissions** - Only grant required permissions
4. **Set SAS token expiry** - Regularly rotate tokens
5. **Use container-level SAS** - More secure than account-level
6. **Enable CORS** - Configure CORS in Azure Portal if accessing from browser

## Troubleshooting

### CORS Errors
If you get CORS errors, configure CORS in Azure Portal:
1. Go to your Storage Account
2. Click "Resource sharing (CORS)" under Settings
3. Add your domain to "Allowed origins"
4. Set allowed methods: GET, PUT, POST, DELETE
5. Set allowed headers: *

### Authentication Errors
- Verify your connection string or SAS token is correct
- Check that the SAS token hasn't expired
- Ensure the container name is correct
- Verify the container exists and is accessible

### Container Not Found
- Make sure the container exists in Azure Portal
- Check container name spelling
- Verify your credentials have access to the container
