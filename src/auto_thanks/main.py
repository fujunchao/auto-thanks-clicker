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
    from .models import Config
    from .config_manager import ConfigManager
    from .window_capture import WindowCapture
    from .image_recognizer import ImageRecognizer
    from .auto_clicker import AutoClicker
    from .task_orchestrator import TaskOrchestrator
    from .task_scheduler import TaskScheduler
    from .tray_icon import TrayIcon
    from .settings_window import SettingsWindow
    from .logger import setup_logging, shutdown_logging
    from .resource_path import get_config_path, get_templates_dir, get_log_path, is_bundled
except ImportError:
    from auto_thanks.models import Config
    from auto_thanks.config_manager import ConfigManager
    from auto_thanks.window_capture import WindowCapture
    from auto_thanks.image_recognizer import ImageRecognizer
    from auto_thanks.auto_clicker import AutoClicker
    from auto_thanks.task_orchestrator import TaskOrchestrator
    from auto_thanks.task_scheduler import TaskScheduler
    from auto_thanks.tray_icon import TrayIcon
    from auto_thanks.settings_window import SettingsWindow
    from auto_thanks.logger import setup_logging, shutdown_logging
    from auto_thanks.resource_path import get_config_path, get_templates_dir, get_log_path, is_bundled


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
            self.window_capture = WindowCapture(self.config.window_title)
            self._logger.info(f"Window capture initialized for: '{self.config.window_title}'")

            # Step 4: Initialize image recognizer (use proper templates path)
            templates_dir = str(get_templates_dir()) if self.config.templates_dir == "templates" else self.config.templates_dir
            self.image_recognizer = ImageRecognizer(
                templates_dir=templates_dir,
                confidence_threshold=self.config.confidence_threshold
            )
            self.image_recognizer.load_templates()
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

            # Step 7: Initialize scheduler
            self.scheduler = TaskScheduler(
                orchestrator=self.orchestrator,
                interval_minutes=self.config.check_interval
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
        """Show the settings window as a subprocess."""
        import subprocess
        import sys
        
        try:
            if getattr(sys, 'frozen', False):
                # Running from PyInstaller bundle - use pythonw to run settings
                # Since we can't easily spawn a subprocess with bundled app,
                # we'll use a simpler approach: edit config.json directly
                config_path = self.config_path
                # Open config file with default editor
                import os
                os.startfile(config_path)
                self._logger.info(f"Opened config file: {config_path}")
                # Show notification
                if self.tray_icon:
                    self.tray_icon.show_notification(
                        "Auto Thanks", 
                        "配置文件已打开，编辑后保存并重启程序。"
                    )
            else:
                # Running in development - can use subprocess
                settings_script = os.path.join(
                    os.path.dirname(__file__), 
                    'settings_app.py'
                )
                subprocess.Popen(
                    [sys.executable, settings_script, self.config_path],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
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

        # Update window capture with new window title
        if self.window_capture:
            self.window_capture.window_title = new_config.window_title
            self.window_capture.reset()

        # Update image recognizer with new settings
        if self.image_recognizer:
            self.image_recognizer.templates_dir = new_config.templates_dir
            self.image_recognizer.confidence_threshold = new_config.confidence_threshold
            self.image_recognizer.load_templates()

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
