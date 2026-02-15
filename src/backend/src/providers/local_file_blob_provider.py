from pathlib import Path
from typing import List
from interfaces.blob import IBlob
import logging
logger = logging.getLogger(__name__)


class LocalFileBlobProvider(IBlob):
    """
    Local file system implementation of blob storage using pathlib.
    Stores blobs as files in a configured base directory.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the local file blob provider.
        
        Args:
            base_path: Base directory path for storing blobs
        """
        self.base_path = base_path.resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a blob-style relative path to an absolute file system path.
        Only accepts relative paths without drive letters or absolute components.
        
        Args:
            path: Blob-style relative path (e.g., "characters/hero.json")
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            ValueError: If path is absolute, contains drive letter, or attempts traversal
        """
        # Convert to Path and normalize separators
        blob_path = Path(path.replace("\\", "/"))
        
        # Reject absolute paths (drive letters, UNC paths, or paths starting with /)
        if blob_path.is_absolute():
            raise ValueError(f"Path must be relative, not absolute: {path}")
        
        # Reject paths that try to escape using ..
        if ".." in blob_path.parts:
            raise ValueError(f"Path traversal not allowed: {path}")
        
        # Simple join - no need for resolve() since we've validated it's safe
        return self.base_path / blob_path

    async def read(self, path: str) -> bytes:
        """Read blob data from the local file system."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            logger.warning(f"Blob not found at path: {path}")
            raise FileNotFoundError(f"Blob not found at path: {path}")
        
        if not file_path.is_file():
            logger.warning(f"Path is a directory, not a file: {path}")
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        logger.info(f"Reading blob from path: {path}")
        return file_path.read_bytes()

    async def write(self, path: str, data: bytes) -> None:
        """Write blob data to the local file system."""
        file_path = self._resolve_path(path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing blob to path: {path}")
        file_path.write_bytes(data)

    async def delete(self, path: str) -> None:
        """Delete blob from the local file system."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            logger.warning(f"Blob not found at path: {path}")
            raise FileNotFoundError(f"Blob not found at path: {path}")
        
        if not file_path.is_file():
            logger.warning(f"Path is a directory, not a file: {path}")
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        logger.info(f"Deleting blob at path: {path}")
        file_path.unlink()

    async def exists(self, path: str) -> bool:
        """Check if blob exists in the local file system."""
        try:
            file_path = self._resolve_path(path)
            logger.info(f"File {file_path} exists: {file_path.exists()}"
                        f" and is_file: {file_path.is_file()}")
            return file_path.exists() and file_path.is_file()
        except ValueError:
            logger.warning(f"Invalid path provided for exists check: {path}")
            return False

    async def list(self, prefix: str = "") -> List[str]:
        """List all blobs with the given prefix in the local file system."""
        if prefix:
            # Start from the prefix directory if it exists
            logger.info(f"Listing blobs with prefix: {prefix}")
            search_path = self._resolve_path(prefix)
            if not search_path.exists():
                logger.warning(f"Prefix path does not exist: {prefix}")
                return []
        else:
            search_path = self.base_path
        
        # Collect all files recursively
        blobs: List[str] = []
        prefix_path = Path(prefix.replace("\\", "/")) if prefix else Path()
        
        if search_path.is_file():
            # If the prefix points to a file, return just that file
            relative = search_path.relative_to(self.base_path)
            blobs.append(relative.as_posix())
        elif search_path.is_dir():
            # Recursively find all files
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    relative = file_path.relative_to(self.base_path)
                    
                    # Only include if it matches the prefix
                    if not prefix or relative.as_posix().startswith(prefix_path.as_posix()):
                        blobs.append(relative.as_posix())
        
        logger.info(f"Found {len(blobs)} blobs with prefix '{prefix}'")
        return sorted(blobs)

    def get_url(self, path: str) -> str:
        """Get a file:// URL for the blob."""
        file_path = self._resolve_path(path)
        logger.info(f"Getting URL for blob at path: {path} -> {file_path.as_uri()}")
        return file_path.as_uri()
