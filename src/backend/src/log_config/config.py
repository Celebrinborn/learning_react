"""Logging configuration based on app config"""
import logging
import sys
from pathlib import Path

from config import get_config
from .formatters import JSONLFormatter
from .filters import TraceContextFilter


def setup_logging() -> None:
    """
    Configure logging based on application configuration.

    Reads the app config to determine:
    - Output destination (file for dev, stdout for test/prod)
    - Log level (DEBUG for dev, INFO for test/prod)
    - Log directory (used only if output=file)

    This should be called early in application startup, after
    environment variables are loaded but before any logging occurs.
    """
    # Get configuration for current environment
    config = get_config()
    log_config = config["logging"]

    # Create formatter and filter
    formatter = JSONLFormatter()
    trace_filter = TraceContextFilter()

    # Choose handler based on configuration
    if log_config["output"] == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:  # file
        # Create log directory if it doesn't exist
        log_dir = Path(log_config["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create file handler
        log_file = log_dir / "app.jsonl"
        handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')

    # Apply formatter and filter to handler
    handler.setFormatter(formatter)
    handler.addFilter(trace_filter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config["level"])

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add our handler
    root_logger.addHandler(handler)

    # Log startup message
    logging.info(
        "Logging initialized",
        extra={
            "environment": config["env"],
            "output": log_config["output"],
            "level": log_config["level"],
        }
    )
