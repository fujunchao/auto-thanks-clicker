"""Logging configuration module for Auto Thanks Clicker.

This module provides centralized logging configuration with:
- Configurable log format and output
- Log file rotation to prevent excessive disk usage
- Console and file handlers
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


# Default configuration values
DEFAULT_LOG_FILE = "auto_thanks.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_BACKUP_COUNT = 3  # Keep 3 backup files
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_file: str = DEFAULT_LOG_FILE,
    log_level: int = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and setup logging for the application.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        log_format: Format string for log messages
        date_format: Format string for timestamps
        console_output: Whether to also output logs to console
        
    Returns:
        The root logger for the auto_thanks package
    """
    # Get the root logger for our package
    root_logger = logging.getLogger("auto_thanks")
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Set the logging level
    root_logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Optionally add console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    root_logger.propagate = False
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: The name of the module (typically __name__)
        
    Returns:
        A logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Change the logging level for all handlers.
    
    Args:
        level: The new logging level (e.g., logging.DEBUG)
    """
    root_logger = logging.getLogger("auto_thanks")
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


def add_file_handler(
    log_file: str,
    log_level: int = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> RotatingFileHandler:
    """
    Add an additional rotating file handler to the logger.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level for this handler
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        log_format: Format string for log messages
        date_format: Format string for timestamps
        
    Returns:
        The created file handler
    """
    root_logger = logging.getLogger("auto_thanks")
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return file_handler


def shutdown_logging() -> None:
    """
    Properly shutdown logging, closing all handlers.
    
    This should be called when the application exits to ensure
    all log data is flushed and files are properly closed.
    """
    root_logger = logging.getLogger("auto_thanks")
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
