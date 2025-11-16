"""
Logging configuration for Alavista.

Provides structured logging with support for both standard and JSON formats.
"""

import logging
import sys

from alavista.core.config import get_settings


def configure_logging(level: str | None = None, json_format: bool | None = None) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses settings.log_level
        json_format: Enable JSON structured logging.
                    If None, uses settings.json_logs
    """
    settings = get_settings()

    log_level = level or settings.log_level
    use_json = json_format if json_format is not None else settings.json_logs

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level.upper())

    # Set format based on json_format flag
    if use_json:
        # JSON format for structured logging
        # In production, you might want to use python-json-logger or similar
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        # Standard format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Configure logging on module import
configure_logging()
