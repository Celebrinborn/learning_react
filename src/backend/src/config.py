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
    azure_container_name: str  # Single container name (e.g., "data")
    azure_prefix_maps: str  # Folder prefix for maps (e.g., "maps")
    azure_prefix_characters: str  # Folder prefix for characters
    azure_prefix_users: str  # Folder prefix for users
    azure_prefix_homebrew: str  # Folder prefix for homebrew


class AuthConfig(TypedDict):
    auth_mode: Literal["local_fake", "entra_external_id"]
    entra_issuer: str
    entra_audience: str
    entra_jwks_url: str
    entra_required_scopes: str


class LoggingConfig(TypedDict):
    """Logging configuration"""
    output: Literal["file", "stdout"]  # Where logs go
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]  # Min log level
    log_dir: str  # Only used if output=file


class AppConfig(TypedDict):
    env: Literal["dev", "prod"]
    host: str
    port: int
    storage: StorageConfig
    auth: AuthConfig
    logging: LoggingConfig


# Environment-specific configurations
CONFIGS: dict[str, AppConfig] = {
    "dev": {
        "env": "dev",
        "host": "127.0.0.1",
        "port": 8000,
        "storage": {
            "storage_type": "local",
            "local_data_path": "../data",
            "azure_storage_account_url": "",
            "azure_container_name": "data",
            "azure_prefix_maps": "maps",
            "azure_prefix_characters": "characters",
            "azure_prefix_users": "users",
            "azure_prefix_homebrew": "homebrew",
        },
        "auth": {
            "auth_mode": "local_fake",
            "entra_issuer": "",
            "entra_audience": "",
            "entra_jwks_url": "",
            "entra_required_scopes": "",
        },
        "logging": {
            "output": "file",
            "level": "DEBUG",
            "log_dir": "./logs",
        },
    },
    "prod": {
        "env": "prod",
        "host": "0.0.0.0",
        "port": 8000,
        "storage": {
            "storage_type": "azure",
            "local_data_path": "./data",
            "azure_storage_account_url": "https://cacolemadndportal.blob.core.windows.net",
            "azure_container_name": "data",
            "azure_prefix_maps": "maps",
            "azure_prefix_characters": "characters",
            "azure_prefix_users": "users",
            "azure_prefix_homebrew": "homebrew",
        },
        "auth": {
            "auth_mode": "entra_external_id",
            "entra_issuer": "https://<tenant>.ciamlogin.com/<tenant-id>/v2.0",
            "entra_audience": "api://<api-client-id>",
            "entra_jwks_url": "https://<tenant>.ciamlogin.com/<tenant-id>/discovery/v2.0/keys",
            "entra_required_scopes": "api://<api-client-id>/access_as_user",
        },
        "logging": {
            "output": "stdout",
            "level": "INFO",
            "log_dir": "./logs",
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
        "prod": "prod",
        "production": "prod",
    }

    normalized_env = env_map.get(env)
    if normalized_env is None:
        raise ValueError(f"Unknown environment: {env}. Valid: dev, prod")
    
    return CONFIGS[normalized_env]
