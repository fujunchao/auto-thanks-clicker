"""
Resource path utilities for Auto Thanks Clicker.

This module provides utilities for resolving resource paths that work
both in development mode and when bundled with PyInstaller.

When running from a PyInstaller bundle, resources are extracted to a
temporary directory. This module handles the path resolution transparently.
"""

import os
import sys
from pathlib import Path
from typing import Union


def get_base_path() -> Path:
    """
    Get the base path for resource resolution.
    
    When running from a PyInstaller bundle, this returns the path to the
    temporary directory where resources are extracted (_MEIPASS).
    
    When running in development mode, this returns the project root directory.
    
    Returns:
        Path to the base directory for resource resolution
    """
    # Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running in development mode
        # Go up from src/auto_thanks to project root
        return Path(__file__).parent.parent.parent


def get_resource_path(relative_path: Union[str, Path]) -> Path:
    """
    Get the absolute path to a resource file.
    
    This function resolves paths correctly whether running from source
    or from a PyInstaller bundle.
    
    Args:
        relative_path: Path relative to the project root (e.g., "templates/thanks_button.png")
        
    Returns:
        Absolute path to the resource
        
    Example:
        >>> template_path = get_resource_path("templates/thanks_button.png")
        >>> config_path = get_resource_path("config.json")
    """
    base_path = get_base_path()
    return base_path / relative_path


def get_templates_dir() -> Path:
    """
    Get the path to the templates directory.
    
    Returns:
        Absolute path to the templates directory
    """
    return get_resource_path("templates")


def get_config_path(config_filename: str = "config.json") -> Path:
    """
    Get the path to the configuration file.
    
    For bundled applications, the config file is stored in the same
    directory as the executable to allow user modifications.
    
    For development mode, it's in the project root.
    
    Args:
        config_filename: Name of the configuration file
        
    Returns:
        Absolute path to the configuration file
    """
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        # Store config next to the executable for user access
        exe_dir = Path(sys.executable).parent
        return exe_dir / config_filename
    else:
        # Running in development mode
        return get_resource_path(config_filename)


def get_log_path(log_filename: str = "auto_thanks.log") -> Path:
    """
    Get the path to the log file.
    
    For bundled applications, logs are stored in the same directory
    as the executable.
    
    Args:
        log_filename: Name of the log file
        
    Returns:
        Absolute path to the log file
    """
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        exe_dir = Path(sys.executable).parent
        return exe_dir / log_filename
    else:
        # Running in development mode
        return get_resource_path(log_filename)


def is_bundled() -> bool:
    """
    Check if running from a PyInstaller bundle.
    
    Returns:
        True if running from a bundle, False if running from source
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def ensure_templates_dir_exists() -> Path:
    """
    Ensure the templates directory exists.
    
    For bundled applications, this creates the templates directory
    next to the executable if it doesn't exist.
    
    Returns:
        Path to the templates directory
    """
    if is_bundled():
        # For bundled app, create templates dir next to executable
        exe_dir = Path(sys.executable).parent
        templates_dir = exe_dir / "templates"
    else:
        templates_dir = get_templates_dir()
    
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir
