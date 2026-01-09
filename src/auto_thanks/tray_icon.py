"""System tray icon module for Auto Thanks Clicker."""

import logging
import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .task_scheduler import TaskScheduler
    from .config_manager import ConfigManager
except ImportError:
    from auto_thanks.task_scheduler import TaskScheduler
    from auto_thanks.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class TrayIcon:
    """系统托盘图标"""

    # Icon colors
    COLOR_RUNNING = (0, 200, 0)  # Green when running
    COLOR_STOPPED = (200, 0, 0)  # Red when stopped
    ICON_SIZE = 64

    def __init__(
        self,
        scheduler: TaskScheduler,
        config_manager: ConfigManager,
        on_settings_click: Optional[Callable] = None
    ):
        """
        初始化托盘图标

        Args:
            scheduler: 任务调度器
            config_manager: 配置管理器
            on_settings_click: 点击设置时的回调函数
        """
        self.scheduler = scheduler
        self.config_manager = config_manager
        self.on_settings_click = on_settings_click
        self._icon: Optional[pystray.Icon] = None
        self._running = False

    def _create_icon_image(self, is_running: bool) -> Image.Image:
        """
        创建托盘图标图像

        Args:
            is_running: 是否正在运行

        Returns:
            PIL Image 对象
        """
        color = self.COLOR_RUNNING if is_running else self.COLOR_STOPPED
        
        # Create a simple circular icon
        image = Image.new('RGBA', (self.ICON_SIZE, self.ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw outer circle
        margin = 4
        draw.ellipse(
            [margin, margin, self.ICON_SIZE - margin, self.ICON_SIZE - margin],
            fill=color,
            outline=(255, 255, 255)
        )
        
        # Draw "T" letter in center for "Thanks"
        text_color = (255, 255, 255)
        # Simple T shape
        center = self.ICON_SIZE // 2
        draw.rectangle([center - 12, center - 10, center + 12, center - 6], fill=text_color)
        draw.rectangle([center - 3, center - 10, center + 3, center + 12], fill=text_color)
        
        return image

    def _create_menu(self) -> pystray.Menu:
        """
        创建右键菜单

        Returns:
            pystray.Menu 对象
        """
        return pystray.Menu(
            pystray.MenuItem(
                "启动",
                self._on_start,
                visible=lambda item: not self.scheduler.is_running()
            ),
            pystray.MenuItem(
                "停止",
                self._on_stop,
                visible=lambda item: self.scheduler.is_running()
            ),
            pystray.MenuItem(
                "立即执行",
                self._on_run_now
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "设置",
                self._on_settings
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "退出",
                self._on_exit
            )
        )

    def _on_start(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """启动调度器"""
        logger.info("Starting scheduler from tray menu")
        self.scheduler.start()
        self.update_status(True)
        self.show_notification("Auto Thanks", "自动感谢已启动")

    def _on_stop(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """停止调度器"""
        logger.info("Stopping scheduler from tray menu")
        self.scheduler.stop()
        self.update_status(False)
        self.show_notification("Auto Thanks", "自动感谢已停止")

    def _on_run_now(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """立即执行扫描"""
        logger.info("Running scan now from tray menu")
        
        def run_scan():
            try:
                result = self.scheduler.run_now()
                message = f"扫描完成: 点击了 {result.buttons_clicked} 个按钮"
                if result.errors:
                    message += f", {len(result.errors)} 个错误"
                self.show_notification("Auto Thanks", message)
            except Exception as e:
                logger.error(f"Error running scan: {e}")
                self.show_notification("Auto Thanks", f"扫描失败: {e}")
        
        # Run in background thread to avoid blocking
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()

    def _on_settings(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """打开设置窗口"""
        logger.info("Opening settings from tray menu")
        if self.on_settings_click:
            # Run in main thread for tkinter compatibility
            self.on_settings_click()

    def _on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """退出程序"""
        logger.info("Exiting from tray menu")
        self.stop()

    def run(self) -> None:
        """运行托盘图标（阻塞）"""
        if self._running:
            logger.warning("Tray icon is already running")
            return

        logger.info("Starting tray icon")
        
        is_running = self.scheduler.is_running()
        icon_image = self._create_icon_image(is_running)
        
        self._icon = pystray.Icon(
            name="auto_thanks",
            icon=icon_image,
            title="Auto Thanks Clicker",
            menu=self._create_menu()
        )
        
        self._running = True
        self._icon.run()

    def run_detached(self) -> None:
        """在后台线程运行托盘图标（非阻塞）"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def stop(self) -> None:
        """停止托盘图标"""
        if not self._running:
            logger.warning("Tray icon is not running")
            return

        logger.info("Stopping tray icon")
        
        # Stop scheduler if running
        if self.scheduler.is_running():
            self.scheduler.stop()
        
        if self._icon:
            self._icon.stop()
            self._icon = None
        
        self._running = False

    def show_notification(self, title: str, message: str) -> None:
        """
        显示通知

        Args:
            title: 通知标题
            message: 通知内容
        """
        if self._icon:
            try:
                self._icon.notify(message, title)
                logger.debug(f"Notification shown: {title} - {message}")
            except Exception as e:
                logger.warning(f"Failed to show notification: {e}")

    def update_status(self, is_running: bool) -> None:
        """
        更新状态图标

        Args:
            is_running: 是否正在运行
        """
        if self._icon:
            new_icon = self._create_icon_image(is_running)
            self._icon.icon = new_icon
            logger.debug(f"Status icon updated: running={is_running}")

    def is_running(self) -> bool:
        """
        检查托盘图标是否运行中

        Returns:
            True 如果托盘图标正在运行
        """
        return self._running
