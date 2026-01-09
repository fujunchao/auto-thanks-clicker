"""Auto Thanks Clicker - Windows desktop automation tool."""

__version__ = "1.0.0"

from .models import Config, MatchResult, ScanResult
from .config_manager import ConfigManager
from .window_capture import WindowCapture
from .image_recognizer import ImageRecognizer
from .auto_clicker import AutoClicker
from .task_orchestrator import TaskOrchestrator
from .task_scheduler import TaskScheduler
from .logger import setup_logging, get_logger, set_log_level, shutdown_logging
from .tray_icon import TrayIcon
from .settings_window import SettingsWindow
from .main import AutoThanksApp, main
from .resource_path import (
    get_base_path,
    get_resource_path,
    get_templates_dir,
    get_config_path,
    get_log_path,
    is_bundled,
    ensure_templates_dir_exists,
)

__all__ = [
    "Config",
    "MatchResult",
    "ScanResult",
    "ConfigManager",
    "WindowCapture",
    "ImageRecognizer",
    "AutoClicker",
    "TaskOrchestrator",
    "TaskScheduler",
    "setup_logging",
    "get_logger",
    "set_log_level",
    "shutdown_logging",
    "TrayIcon",
    "SettingsWindow",
    "AutoThanksApp",
    "main",
    "get_base_path",
    "get_resource_path",
    "get_templates_dir",
    "get_config_path",
    "get_log_path",
    "is_bundled",
    "ensure_templates_dir_exists",
]
