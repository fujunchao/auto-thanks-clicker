"""Main entry point for Auto Thanks Clicker.

This module initializes all components and starts the application.
"""

import sys
import os
import logging
import threading
from typing import Optional

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import Config, ScanResult
    from .config_manager import ConfigManager
    from .window_capture import WindowCapture
    from .image_recognizer import ImageRecognizer, TemplateDirectoryError
    from .auto_clicker import AutoClicker
    from .task_orchestrator import TaskOrchestrator
    from .task_scheduler import TaskScheduler
    from .tray_icon import TrayIcon
    from .settings_window import SettingsWindow
    from .logger import setup_logging, shutdown_logging
    from .resource_path import get_config_path, get_templates_dir, get_log_path, is_bundled
except ImportError:
    from auto_thanks.models import Config, ScanResult
    from auto_thanks.config_manager import ConfigManager
    from auto_thanks.window_capture import WindowCapture
    from auto_thanks.image_recognizer import ImageRecognizer, TemplateDirectoryError
    from auto_thanks.auto_clicker import AutoClicker
    from auto_thanks.task_orchestrator import TaskOrchestrator
    from auto_thanks.task_scheduler import TaskScheduler
    from auto_thanks.tray_icon import TrayIcon
    from auto_thanks.settings_window import SettingsWindow
    from auto_thanks.logger import setup_logging, shutdown_logging
    from auto_thanks.resource_path import get_config_path, get_templates_dir, get_log_path, is_bundled


def show_error_dialog(title: str, message: str) -> None:
    """
    Display a user-friendly error dialog using tkinter.
    
    Args:
        title: Dialog window title
        message: Error message to display
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Show error message box
        messagebox.showerror(title, message)
        
        # Destroy the root window
        root.destroy()
    except Exception:
        # Fallback to console output if tkinter fails
        print(f"ERROR: {title}")
        print(message)


class AutoThanksApp:
    """Main application class that coordinates all components."""

    def __init__(self, config_path: str = None):
        """
        Initialize the application.

        Args:
            config_path: Path to the configuration file (auto-detected if None)
        """
        # Auto-detect config path based on running mode
        if config_path is None:
            self.config_path = str(get_config_path())
        else:
            self.config_path = config_path
            
        self.config_manager: Optional[ConfigManager] = None
        self.config: Optional[Config] = None
        self.window_capture: Optional[WindowCapture] = None
        self.image_recognizer: Optional[ImageRecognizer] = None
        self.auto_clicker: Optional[AutoClicker] = None
        self.orchestrator: Optional[TaskOrchestrator] = None
        self.scheduler: Optional[TaskScheduler] = None
        self.tray_icon: Optional[TrayIcon] = None
        self.settings_window: Optional[SettingsWindow] = None
        self._logger: Optional[logging.Logger] = None

    def initialize(self) -> bool:
        """
        Initialize all application components.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Step 1: Load configuration
            self.config_manager = ConfigManager(self.config_path)
            self.config = self.config_manager.load()

            # Step 2: Setup logging (use proper path for bundled app)
            log_file = str(get_log_path(self.config.log_file))
            self._logger = setup_logging(
                log_file=log_file,
                console_output=True
            )
            self._logger.info("Auto Thanks Clicker starting...")
            self._logger.info(f"Running in {'bundled' if is_bundled() else 'development'} mode")
            self._logger.info(f"Configuration loaded from: {self.config_path}")

            # Step 3: Initialize window capture module
            self.window_capture = WindowCapture(
                window_title=self.config.window_title,
                process_name=self.config.process_name
            )
            self._logger.info(
                f"Window capture initialized for: title='{self.config.window_title}', "
                f"process='{self.config.process_name}'"
            )

            # Step 4: Initialize image recognizer (use proper templates path)
            templates_dir = str(get_templates_dir()) if self.config.templates_dir == "templates" else self.config.templates_dir
            self.image_recognizer = ImageRecognizer(
                templates_dir=templates_dir,
                confidence_threshold=self.config.confidence_threshold
            )
            try:
                self.image_recognizer.load_templates()
            except TemplateDirectoryError as e:
                self._logger.error(f"Template directory error: {e}")
                show_error_dialog(
                    "模板目录错误 - Auto Thanks Clicker",
                    str(e)
                )
                return False
            self._logger.info(f"Image recognizer initialized with templates from: {templates_dir}")

            # Step 5: Initialize auto clicker
            self.auto_clicker = AutoClicker(
                click_delay=self.config.click_delay,
                scroll_amount=self.config.scroll_count
            )
            self._logger.info("Auto clicker initialized")

            # Step 6: Initialize task orchestrator
            self.orchestrator = TaskOrchestrator(
                window_capture=self.window_capture,
                image_recognizer=self.image_recognizer,
                auto_clicker=self.auto_clicker,
                config=self.config
            )
            self._logger.info("Task orchestrator initialized")

            # Step 7: Initialize scheduler with scan complete callback
            self.scheduler = TaskScheduler(
                orchestrator=self.orchestrator,
                interval_minutes=self.config.check_interval,
                on_scan_complete=self._on_scan_complete
            )
            self._logger.info(f"Scheduler initialized with interval: {self.config.check_interval} minutes")

            # Step 8: Initialize settings window
            self.settings_window = SettingsWindow(
                config_manager=self.config_manager,
                on_save=self._on_config_saved
            )

            # Step 9: Initialize tray icon
            self.tray_icon = TrayIcon(
                scheduler=self.scheduler,
                config_manager=self.config_manager,
                on_settings_click=self._show_settings
            )
            self._logger.info("Tray icon initialized")

            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to initialize application: {e}")
            else:
                print(f"Failed to initialize application: {e}")
            return False

    def _show_settings(self) -> None:
        """Show the settings window in a thread-safe manner.
        
        This method works in both development and bundled (PyInstaller) modes.
        It runs the tkinter settings window in a separate thread to avoid
        blocking the tray icon's event loop.
        """
        try:
            # Check if settings window is already open
            if self.settings_window and self.settings_window.is_open():
                self._logger.info("Settings window already open, skipping")
                return
            
            # Run settings window in a separate thread
            # tkinter can run in a non-main thread as long as we create
            # a new Tk instance in that thread
            def show_settings_thread():
                try:
                    self._logger.info("Opening settings window")
                    self.settings_window.show()
                except Exception as e:
                    self._logger.error(f"Error in settings window: {e}")
            
            settings_thread = threading.Thread(
                target=show_settings_thread,
                daemon=True,
                name="SettingsWindowThread"
            )
            settings_thread.start()
            
        except Exception as e:
            self._logger.error(f"Failed to open settings: {e}")

    def _on_config_saved(self, new_config: Config) -> None:
        """
        Handle configuration changes.

        Args:
            new_config: The new configuration
        """
        self._logger.info("Configuration updated, applying changes...")
        self.config = new_config

        # Update window capture with new window title and process name
        if self.window_capture:
            self.window_capture.window_title = new_config.window_title
            self.window_capture.process_name = new_config.process_name
            self.window_capture.reset()

        # Update image recognizer with new settings
        if self.image_recognizer:
            self.image_recognizer.templates_dir = new_config.templates_dir
            self.image_recognizer.confidence_threshold = new_config.confidence_threshold
            try:
                self.image_recognizer.load_templates()
            except TemplateDirectoryError as e:
                self._logger.error(f"Template directory error after config change: {e}")
                show_error_dialog(
                    "模板目录错误 - Auto Thanks Clicker",
                    str(e)
                )

        # Update auto clicker with new settings
        if self.auto_clicker:
            self.auto_clicker.click_delay = new_config.click_delay
            self.auto_clicker.scroll_amount = new_config.scroll_count

        # Update orchestrator config
        if self.orchestrator:
            self.orchestrator.config = new_config

        # Update scheduler interval
        if self.scheduler:
            self.scheduler.set_interval(new_config.check_interval)

        self._logger.info("Configuration changes applied successfully")

    def _on_scan_complete(self, result: ScanResult) -> None:
        """
        Handle scan completion and show notification if buttons were clicked.

        Args:
            result: The ScanResult from the completed scan
        """
        # Only show notification if buttons were clicked
        if result.buttons_clicked > 0:
            message = f"已点击 {result.buttons_clicked} 个谢谢按钮"
            if self.tray_icon:
                self.tray_icon.show_notification("Auto Thanks", message)
            self._logger.info(f"Scan complete notification: {message}")

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if not self.initialize():
            return 1

        try:
            self._logger.info("Starting scheduler...")
            self.scheduler.start()

            self._logger.info("Starting tray icon (blocking)...")
            self.tray_icon.run()

            return 0

        except KeyboardInterrupt:
            self._logger.info("Received keyboard interrupt, shutting down...")
            return 0

        except Exception as e:
            self._logger.error(f"Application error: {e}")
            return 1

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the application and cleanup resources."""
        if self._logger:
            self._logger.info("Shutting down Auto Thanks Clicker...")

        # Stop scheduler
        if self.scheduler and self.scheduler.is_running():
            self.scheduler.stop()

        # Stop tray icon
        if self.tray_icon and self.tray_icon.is_running():
            self.tray_icon.stop()

        # Shutdown logging
        shutdown_logging()


def main() -> int:
    """
    Main entry point function.

    Returns:
        Exit code
    """
    app = AutoThanksApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
