from pathlib import Path
from typing import List
from dnd_backend.interfaces.blob import IBlobStorage


class LocalFileBlobProvider(IBlobStorage):
    """
    Local file system implementation of blob storage using pathlib.
    Stores blobs as files in a configured base directory.
    """

    def __init__(self, base_path: str):
        """
        Initialize the local file blob provider.
        
        Args:
            base_path: Base directory path for storing blobs
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a relative blob path to an absolute file system path.
        Ensures the path is within the base directory for security.
        
        Args:
            path: Relative blob path
            
        Returns:
            Resolved absolute Path object
        """
        # Remove leading slashes and normalize
        clean_path = path.lstrip("/").replace("\\", "/")
        full_path = (self.base_path / clean_path).resolve()
        
        # Ensure the resolved path is within base_path (prevent directory traversal)
        if not str(full_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path '{path}' is outside the base directory")
        
        return full_path

    async def read(self, path: str) -> bytes:
        """Read blob data from the local file system."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Blob not found at path: {path}")
        
        if not file_path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        return file_path.read_bytes()

    async def write(self, path: str, data: bytes) -> None:
        """Write blob data to the local file system."""
        file_path = self._resolve_path(path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_bytes(data)

    async def delete(self, path: str) -> None:
        """Delete blob from the local file system."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Blob not found at path: {path}")
        
        if not file_path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        file_path.unlink()

    async def exists(self, path: str) -> bool:
        """Check if blob exists in the local file system."""
        try:
            file_path = self._resolve_path(path)
            return file_path.exists() and file_path.is_file()
        except ValueError:
            return False

    async def list(self, prefix: str = "") -> List[str]:
        """List all blobs with the given prefix in the local file system."""
        if prefix:
            # Start from the prefix directory if it exists
            search_path = self._resolve_path(prefix)
            if not search_path.exists():
                return []
        else:
            search_path = self.base_path
        
        # Collect all files recursively
        blobs = []
        if search_path.is_file():
            # If the prefix points to a file, return just that file
            relative = search_path.relative_to(self.base_path)
            blobs.append(str(relative).replace("\\", "/"))
        elif search_path.is_dir():
            # Recursively find all files
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    relative = file_path.relative_to(self.base_path)
                    blob_path = str(relative).replace("\\", "/")
                    
                    # Only include if it matches the prefix
                    if not prefix or blob_path.startswith(prefix.replace("\\", "/")):
                        blobs.append(blob_path)
        
        return sorted(blobs)

    def get_url(self, path: str) -> str:
        """Get a file:// URL for the blob."""
        file_path = self._resolve_path(path)
        return file_path.as_uri()
