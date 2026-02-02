"""
Environment configuration loader.
Loads environment variables from the appropriate .env file based on APP_ENV.
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_environment() -> str:
    """
    Load environment variables from the appropriate .env file.
    
    Uses APP_ENV environment variable to determine which file to load:
    - APP_ENV=dev or unset: loads .env.dev (if exists)
    - APP_ENV=test: loads .env.test
    - APP_ENV=prod: loads .env.prod
    
    Returns:
        The environment name that was loaded
    """
    app_env = os.getenv("APP_ENV", "dev").lower()
    
    # Map environment names to file names
    env_file_map = {
        "dev": ".env.dev",
        "development": ".env.dev",
        "test": ".env.test",
        "testing": ".env.test",
        "prod": ".env.prod",
        "production": ".env.prod",
    }
    
    env_file = env_file_map.get(app_env, ".env.dev")
    
    # Get the backend directory (where this file lives)
    backend_dir = Path(__file__).parent.parent.parent
    env_path = backend_dir / env_file
    
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        # Fallback: try to load .env if it exists
        fallback_path = backend_dir / ".env"
        if fallback_path.exists():
            load_dotenv(fallback_path, override=True)
    
    return app_env
