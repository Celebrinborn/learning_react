"""
Builder module for dependency injection.
This is the only module that should be aware of concrete provider implementations.
All other modules should depend only on interfaces.
"""

from pathlib import Path
from interfaces.blob import IBlobStorage
from providers.local_file_blob import LocalFileBlobProvider


class StorageBuilder:
    """
    Builder class responsible for instantiating storage providers.
    Centralizes provider creation and configuration.
    """

    def __init__(self, base_data_path: str = "./data"):
        """
        Initialize the storage builder.
        
        Args:
            base_data_path: Base path for local file storage
        """
        self.base_data_path = Path(base_data_path)

    def build_blob_storage(self, storage_type: str = "local") -> IBlobStorage:
        """
        Build and return a blob storage provider.
        
        Args:
            storage_type: Type of storage provider ("local" or "azure")
            
        Returns:
            IBlobStorage implementation
            
        Raises:
            ValueError: If storage_type is not supported
        """
        if storage_type == "local":
            return LocalFileBlobProvider(str(self.base_data_path))
        elif storage_type == "azure":
            # Future implementation
            raise NotImplementedError("Azure blob storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    def build_map_blob_storage(self) -> IBlobStorage:
        """
        Build blob storage specifically for maps.
        
        Returns:
            IBlobStorage implementation configured for maps
        """
        maps_path = self.base_data_path / "maps"
        return LocalFileBlobProvider(str(maps_path))

    def build_character_blob_storage(self) -> IBlobStorage:
        """
        Build blob storage specifically for characters.
        
        Returns:
            IBlobStorage implementation configured for characters
        """
        characters_path = self.base_data_path / "characters"
        return LocalFileBlobProvider(str(characters_path))
