"""
Application configuration.
All settings are defined here in a dict per environment.
The builder reads from this to create objects.
"""

import os
from typing import Literal, TypedDict


class StorageConfig(TypedDict):
    storage_type: Literal["local", "azure"]
    local_data_path: str
    azure_storage_account_url: str  # e.g., https://<account>.blob.core.windows.net
    azure_container_maps: str
    azure_container_characters: str
    azure_container_users: str


class AuthConfig(TypedDict):
    auth_mode: Literal["local_fake", "entra_external_id"]
    entra_issuer: str
    entra_audience: str
    entra_jwks_url: str
    entra_required_scopes: str


class AppConfig(TypedDict):
    env: Literal["dev", "test", "prod"]
    host: str
    port: int
    storage: StorageConfig
    auth: AuthConfig


# Environment-specific configurations
CONFIGS: dict[str, AppConfig] = {
    "dev": {
        "env": "dev",
        "host": "127.0.0.1",
        "port": 8000,
        "storage": {
            "storage_type": "local",
            "local_data_path": "./data",
            "azure_storage_account_url": "",
            "azure_container_maps": "maps",
            "azure_container_characters": "characters",
            "azure_container_users": "users",
        },
        "auth": {
            "auth_mode": "local_fake",
            "entra_issuer": "",
            "entra_audience": "",
            "entra_jwks_url": "",
            "entra_required_scopes": "",
        },
    },
    "test": {
        "env": "test",
        "host": "0.0.0.0",
        "port": 8000,
        "storage": {
            "storage_type": "azure",
            "local_data_path": "./data",
            "azure_storage_account_url": "https://<storage-account-test>.blob.core.windows.net",
            "azure_container_maps": "maps-test",
            "azure_container_characters": "characters-test",
            "azure_container_users": "users-test",
        },
        "auth": {
            "auth_mode": "entra_external_id",
            "entra_issuer": "https://<tenant>.ciamlogin.com/<tenant-id>/v2.0",
            "entra_audience": "api://<api-client-id>",
            "entra_jwks_url": "https://<tenant>.ciamlogin.com/<tenant-id>/discovery/v2.0/keys",
            "entra_required_scopes": "api://<api-client-id>/access_as_user",
        },
    },
    "prod": {
        "env": "prod",
        "host": "0.0.0.0",
        "port": 8000,
        "storage": {
            "storage_type": "azure",
            "local_data_path": "./data",
            "azure_storage_account_url": "https://<storage-account-prod>.blob.core.windows.net",
            "azure_container_maps": "maps",
            "azure_container_characters": "characters",
            "azure_container_users": "users",
        },
        "auth": {
            "auth_mode": "entra_external_id",
            "entra_issuer": "https://<tenant>.ciamlogin.com/<tenant-id>/v2.0",
            "entra_audience": "api://<api-client-id>",
            "entra_jwks_url": "https://<tenant>.ciamlogin.com/<tenant-id>/discovery/v2.0/keys",
            "entra_required_scopes": "api://<api-client-id>/access_as_user",
        },
    },
}


def get_config(env: str | None = None) -> AppConfig:
    """
    Get configuration for the specified environment.
    
    Args:
        env: Environment name. If None, reads from APP_ENV env var (defaults to "dev").
        
    Returns:
        AppConfig for the specified environment.
        
    Raises:
        ValueError: If environment is not recognized.
    """
    if env is None:
        env = os.getenv("APP_ENV", "dev").lower()
    
    # Normalize environment names
    env_map = {
        "dev": "dev",
        "development": "dev",
        "test": "test",
        "testing": "test",
        "prod": "prod",
        "production": "prod",
    }
    
    normalized_env = env_map.get(env)
    if normalized_env is None:
        raise ValueError(f"Unknown environment: {env}. Valid: dev, test, prod")
    
    return CONFIGS[normalized_env]
