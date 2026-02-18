"""
Builder module for dependency injection.
This is the only module that should be aware of concrete provider implementations.
All other modules should depend only on interfaces.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from config import get_config, AppConfig
from interfaces.blob import IBlob
from interfaces.auth.auth import iAuthentication, iAuthorization
from providers.local_file_blob_provider import LocalFileBlobProvider
from providers.azure_blob_provider import AzureBlobProvider
from providers.auth.authentication_provider import EntraAuthProvider
from providers.auth.authorization_provider import HardcodedAuthorizationProvider

if TYPE_CHECKING:
    from dependencies.authentication import AuthenticationDependency
    from dependencies.authorization import AuthorizationFactory, GetRolesDependency


class AppBuilder:
    """
    Builder class responsible for instantiating providers.
    Centralizes provider creation and configuration.
    """

    def __init__(self, config: AppConfig | None = None):
        """
        Initialize the builder.

        Args:
            config: Application configuration. If None, loads from APP_ENV.
        """
        self.config = config or get_config()
        self.storage_config = self.config["storage"]
        self.base_data_path = Path(self.storage_config["local_data_path"])

    def build_auth_provider(self) -> EntraAuthProvider:
        """
        Build and return an auth provider based on config.

        Returns:
            EntraAuthProvider instance
        """
        auth_config = self.config["auth"]
        return EntraAuthProvider(
            issuer=auth_config["entra_issuer"],
            audience=auth_config["entra_audience"],
            jwks_url=auth_config["entra_jwks_url"],
        )

    def build_blob_storage(self, storage_type: str | None = None) -> IBlob:
        """
        Build and return a blob storage provider.
        
        Args:
            storage_type: Type of storage provider ("local" or "azure").
                         If None, uses config value.
            
        Returns:
            IBlobStorage implementation
            
        Raises:
            ValueError: If storage_type is not supported
        """
        storage_type = storage_type or self.storage_config["storage_type"]
        
        if storage_type == "local":
            return LocalFileBlobProvider(self.base_data_path)
        elif storage_type == "azure":
            return AzureBlobProvider(
                account_url=self.storage_config["azure_storage_account_url"],
                container_name=self.storage_config["azure_container_name"],
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    def build_map_blob_storage(self) -> IBlob:
        """
        Build blob storage specifically for maps.

        Returns:
            IBlobStorage implementation configured for maps
        """
        if self.storage_config["storage_type"] == "azure":
            return AzureBlobProvider(
                account_url=self.storage_config["azure_storage_account_url"],
                container_name=self.storage_config["azure_container_name"],
                prefix=self.storage_config["azure_prefix_maps"],
            )

        maps_path = self.base_data_path / self.storage_config["azure_prefix_maps"]
        return LocalFileBlobProvider(maps_path)

    def build_character_blob_storage(self) -> IBlob:
        """
        Build blob storage specifically for characters.

        Returns:
            IBlobStorage implementation configured for characters
        """
        if self.storage_config["storage_type"] == "azure":
            return AzureBlobProvider(
                account_url=self.storage_config["azure_storage_account_url"],
                container_name=self.storage_config["azure_container_name"],
                prefix=self.storage_config["azure_prefix_characters"],
            )

        characters_path = self.base_data_path / self.storage_config["azure_prefix_characters"]
        return LocalFileBlobProvider(characters_path)

    def build_user_blob_storage(self) -> IBlob:
        """
        Build blob storage specifically for user data.

        Returns:
            IBlobStorage implementation configured for users
        """
        if self.storage_config["storage_type"] == "azure":
            return AzureBlobProvider(
                account_url=self.storage_config["azure_storage_account_url"],
                container_name=self.storage_config["azure_container_name"],
                prefix=self.storage_config["azure_prefix_users"],
            )

        users_path = self.base_data_path / self.storage_config["azure_prefix_users"]
        return LocalFileBlobProvider(users_path)

    def build_homebrew_blob_storage(self) -> IBlob:
        """
        Build blob storage specifically for homebrew content.

        Returns:
            IBlobStorage implementation configured for homebrew
        """
        if self.storage_config["storage_type"] == "azure":
            return AzureBlobProvider(
                account_url=self.storage_config["azure_storage_account_url"],
                container_name=self.storage_config["azure_container_name"],
                prefix=self.storage_config["azure_prefix_homebrew"],
            )

        homebrew_path = self.base_data_path / self.storage_config["azure_prefix_homebrew"]
        return LocalFileBlobProvider(homebrew_path)
    
    def build_authentication_dependency(self) -> AuthenticationDependency:
        """
        Build the FastAPI authentication dependency.
        """
        from dependencies.authentication import build_authentication_dependency
        authentication_provider: iAuthentication = self.build_auth_provider()
        return build_authentication_dependency(
            authenticator=authentication_provider
        )

    def build_authorization_service(self) -> iAuthorization:
        """
        Build the authorization service implementation.
        """
        return HardcodedAuthorizationProvider()

    def build_require_cnf_roles(self) -> AuthorizationFactory:
        """
        Build the authorization dependency factory used by routes.
        """
        from dependencies.authorization import build_authorization_factory
        authenticate = self.build_authentication_dependency()
        authorizer = self.build_authorization_service()

        return build_authorization_factory(
            authorizer=authorizer,
            authenticate=authenticate,
        )

    def build_get_roles_dependency(self) -> GetRolesDependency:
        """
        Build a FastAPI dependency that returns the roles for the authenticated principal.
        """
        from dependencies.authorization import build_get_roles_dependency
        authenticate = self.build_authentication_dependency()
        authorizer = self.build_authorization_service()

        return build_get_roles_dependency(
            authorizer=authorizer,
            authenticate=authenticate,
        )