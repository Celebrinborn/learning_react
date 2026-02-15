from abc import ABC, abstractmethod
from typing import List


class IBlob(ABC):
    """
    Interface for blob storage operations.
    Defines the contract for reading/writing binary data.
    """

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """
        Read blob data from the given path.

        Args:
            path: Path to the blob

        Returns:
            Blob data as bytes

        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        pass

    @abstractmethod
    async def write(self, path: str, data: bytes) -> None:
        """
        Write blob data to the given path.

        Args:
            path: Path where to write the blob
            data: Binary data to write
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> None:
        """
        Delete blob at the given path.

        Args:
            path: Path to the blob to delete

        Raises:
            FileNotFoundError: If the blob doesn't exist
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if a blob exists at the given path.

        Args:
            path: Path to check

        Returns:
            True if blob exists, False otherwise
        """
        pass

    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """
        List all blobs with the given prefix.

        Args:
            prefix: Path prefix to filter blobs (empty string for all)

        Returns:
            List of blob paths
        """
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        """
        Get a URL/URI for accessing the blob.

        Args:
            path: Path to the blob

        Returns:
            URL or file path as string
        """
        pass
