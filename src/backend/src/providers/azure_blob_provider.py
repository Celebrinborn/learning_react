import logging
from typing import List

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

from interfaces.blob import IBlob

logger = logging.getLogger(__name__)

class AzureBlobProvider(IBlob):
    """
    Azure Blob Storage implementation of IBlobStorage.
    Uses DefaultAzureCredential for Managed Identity authentication.
    Supports folder prefixes within a single container.
    """

    def __init__(self, account_url: str, container_name: str, prefix: str = ""):
        """
        Initialize Azure Blob Provider.

        Args:
            account_url: Azure storage account URL (https://<account>.blob.core.windows.net)
            container_name: Name of the blob container (e.g., "data")
            prefix: Folder prefix within container (e.g., "maps" becomes "maps/")
        """
        self.account_url = account_url
        self.container_name = container_name
        # Ensure prefix ends with / if not empty
        self.prefix = prefix.rstrip('/') + '/' if prefix else ""

        # Use DefaultAzureCredential for Managed Identity in Container Apps
        # Falls back to Azure CLI credentials for local development
        credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        self.container_client: ContainerClient = self.blob_service_client.get_container_client(
            container_name
        )

    def _full_path(self, path: str) -> str:
        """
        Get the full blob path including prefix.

        Args:
            path: Relative path within this provider's scope

        Returns:
            Full blob path with prefix
        """
        # Normalize path separators and remove leading slash
        normalized = path.replace("\\", "/").lstrip("/")
        return f"{self.prefix}{normalized}"

    def _strip_prefix(self, full_path: str) -> str:
        """
        Strip the prefix from a full blob path.

        Args:
            full_path: Full blob path including prefix

        Returns:
            Relative path without prefix
        """
        if self.prefix and full_path.startswith(self.prefix):
            return full_path[len(self.prefix):]
        return full_path

    async def read(self, path: str) -> bytes:
        """
        Read blob data from Azure Storage.

        Args:
            path: Relative path to the blob

        Returns:
            Blob data as bytes

        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(self._full_path(path))
            download_stream = blob_client.download_blob()
            result = download_stream.readall()
            logger.info(f"Read blob at path: {path} (size={len(result)} bytes)")
            return result
        except ResourceNotFoundError:
            logger.error(f"Blob not found at path: {path}")
            raise FileNotFoundError(f"Blob not found at path: {path}")

    async def write(self, path: str, data: bytes) -> None:
        """
        Write blob data to Azure Storage.

        Args:
            path: Relative path where to write the blob
            data: Binary data to write
        """
        blob_client = self.container_client.get_blob_client(self._full_path(path))
        blob_client.upload_blob(data, overwrite=True)

    async def delete(self, path: str) -> None:
        """
        Delete blob from Azure Storage.

        Args:
            path: Relative path to the blob to delete

        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(self._full_path(path))
            blob_client.delete_blob()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found at path: {path}")

    async def exists(self, path: str) -> bool:
        """
        Check if a blob exists in Azure Storage.

        Args:
            path: Relative path to check

        Returns:
            True if blob exists, False otherwise
        """
        blob_client = self.container_client.get_blob_client(self._full_path(path))
        result = blob_client.exists()
        logger.info(f"Checked existence for blob at path: {path} (exists={result})")
        return result

    async def list(self, prefix: str = "") -> List[str]:
        """
        List all blobs with the given prefix.

        Args:
            prefix: Additional path prefix to filter blobs (empty string for all)

        Returns:
            List of blob paths (relative to this provider's prefix)
        """
        # Combine provider prefix with the requested prefix
        full_prefix = self._full_path(prefix) if prefix else self.prefix

        blobs: List[str] = []
        blob_list = self.container_client.list_blobs(
            name_starts_with=full_prefix if full_prefix else None
        )

        for blob in blob_list:
            # Strip the provider's prefix from the blob name
            relative_path = self._strip_prefix(blob.name)
            blobs.append(relative_path)

        logger.info(f"Listed blobs with prefix: {prefix} (found {len(blobs)} blobs)")
        return sorted(blobs)

    def get_url(self, path: str) -> str:
        """
        Get the URL for the blob.

        Args:
            path: Relative path to the blob

        Returns:
            Full URL to the blob
        """
        full_path = self._full_path(path)
        url = f"{self.account_url}/{self.container_name}/{full_path}"
        logger.info(f"Generated URL for blob at path: {path} -> {url}")
        return url
