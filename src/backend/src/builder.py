"""
Builder module for dependency injection.
This is the only module that should be aware of concrete provider implementations.
All other modules should depend only on interfaces.
"""

import os
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
        self.storage_type = os.getenv("STORAGE_TYPE", "local")
        
        # Azure Blob Storage container names (used when storage_type == "azure")
        self.azure_container_maps = os.getenv("AZURE_BLOB_CONTAINER_MAPS", "maps")
        self.azure_container_characters = os.getenv("AZURE_BLOB_CONTAINER_CHARACTERS", "characters")
        self.azure_container_users = os.getenv("AZURE_BLOB_CONTAINER_USERS", "users")

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
            return LocalFileBlobProvider(self.base_data_path)
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
        if self.storage_type == "azure":
            # Future: return AzureBlobProvider(container_name=self.azure_container_maps)
            raise NotImplementedError("Azure blob storage not yet implemented")
        
        maps_path = self.base_data_path / "maps"
        return LocalFileBlobProvider(maps_path)

    def build_character_blob_storage(self) -> IBlobStorage:
        """
        Build blob storage specifically for characters.
        
        Returns:
            IBlobStorage implementation configured for characters
        """
        if self.storage_type == "azure":
            # Future: return AzureBlobProvider(container_name=self.azure_container_characters)
            raise NotImplementedError("Azure blob storage not yet implemented")
        
        characters_path = self.base_data_path / "characters"
        return LocalFileBlobProvider(characters_path)

    def build_user_blob_storage(self) -> IBlobStorage:
        """
        Build blob storage specifically for user data.
        
        Returns:
            IBlobStorage implementation configured for users
        """
        if self.storage_type == "azure":
            # Future: return AzureBlobProvider(container_name=self.azure_container_users)
            raise NotImplementedError("Azure blob storage not yet implemented")
        
        users_path = self.base_data_path / "users"
        return LocalFileBlobProvider(users_path)
