"""Task Orchestrator module for coordinating the auto-thanks workflow."""

import time
import logging
from datetime import datetime
from typing import Tuple, Optional, List

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import Config, MatchResult, ScanResult
    from .window_capture import WindowCapture
    from .image_recognizer import ImageRecognizer
    from .auto_clicker import AutoClicker
except ImportError:
    from auto_thanks.models import Config, MatchResult, ScanResult
    from auto_thanks.window_capture import WindowCapture
    from auto_thanks.image_recognizer import ImageRecognizer
    from auto_thanks.auto_clicker import AutoClicker

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """任务协调器，协调各模块完成自动感谢任务"""

    # Default tabs to check
    DEFAULT_TABS = ["赞", "关注"]
    
    # Wait times (in seconds)
    CONTENT_LOAD_WAIT = 1.0
    REFRESH_WAIT = 0.5
    TAB_SWITCH_WAIT = 0.8

    def __init__(
        self,
        window_capture: WindowCapture,
        image_recognizer: ImageRecognizer,
        auto_clicker: AutoClicker,
        config: Config
    ):
        """
        初始化任务协调器

        Args:
            window_capture: 窗口捕获模块
            image_recognizer: 图像识别模块
            auto_clicker: 自动点击模块
            config: 应用配置
        """
        self.window_capture = window_capture
        self.image_recognizer = image_recognizer
        self.auto_clicker = auto_clicker
        self.config = config

    def run_scan_cycle(self) -> ScanResult:
        """
        执行一次完整的扫描和点击循环

        Returns:
            扫描结果
        """
        result = ScanResult(scan_time=datetime.now())
        
        logger.info("Starting scan cycle")
        
        # Step 1: Find and validate target window
        hwnd = self.window_capture.find_window()
        if not hwnd:
            error_msg = f"Target window not found: {self.window_capture.window_title}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Step 2: Check if window is visible
        if not self.window_capture.is_window_visible():
            error_msg = "Target window is not visible (minimized or hidden)"
            logger.warning(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Step 3: Get window position for coordinate calculations
        window_rect = self.window_capture.get_window_rect()
        if not window_rect:
            error_msg = "Failed to get window position"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Step 4: Process each tab
        for tab_name in self.DEFAULT_TABS:
            try:
                found, clicked = self.process_tab(tab_name, window_rect)
                result.tabs_checked.append(tab_name)
                result.buttons_found += found
                result.buttons_clicked += clicked
            except Exception as e:
                error_msg = f"Error processing tab '{tab_name}': {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        logger.info(
            f"Scan cycle complete: {result.buttons_clicked}/{result.buttons_found} "
            f"buttons clicked in {len(result.tabs_checked)} tabs"
        )
        
        return result

    def process_tab(
        self, 
        tab_name: str, 
        window_rect: Tuple[int, int, int, int]
    ) -> Tuple[int, int]:
        """
        处理单个标签页

        Args:
            tab_name: 标签名称（"赞" 或 "关注"）
            window_rect: 窗口位置 (left, top, right, bottom)

        Returns:
            (找到的按钮数, 点击的按钮数)
        """
        logger.info(f"Processing tab: {tab_name}")
        
        window_offset = (window_rect[0], window_rect[1])
        buttons_found = 0
        buttons_clicked = 0
        
        # Step 1: Capture screenshot to find tab buttons
        screenshot = self.window_capture.capture_screenshot()
        if screenshot is None:
            logger.error("Failed to capture screenshot for tab detection")
            return (0, 0)
        
        # Step 2: Find and click the target tab
        tab_buttons = self.image_recognizer.find_tab_buttons(screenshot)
        if tab_name in tab_buttons:
            tab_match = tab_buttons[tab_name]
            logger.debug(f"Found tab '{tab_name}' at ({tab_match.x}, {tab_match.y})")
            self.auto_clicker.click_button(tab_match, window_offset)
            time.sleep(self.TAB_SWITCH_WAIT)
        else:
            logger.warning(f"Tab '{tab_name}' not found, proceeding with current view")
        
        # Step 3: Refresh content by scrolling
        self.refresh_content(window_rect)
        time.sleep(self.CONTENT_LOAD_WAIT)
        
        # Step 4: Capture fresh screenshot after refresh
        screenshot = self.window_capture.capture_screenshot()
        if screenshot is None:
            logger.error("Failed to capture screenshot after refresh")
            return (0, 0)
        
        # Step 5: Find divider line
        divider_y = self.image_recognizer.find_divider_line(screenshot)
        if divider_y is not None:
            logger.info(f"Found divider line at y={divider_y}")
        else:
            logger.info("No divider line found, will process all visible buttons")
        
        # Step 6: Find thanks buttons
        thanks_buttons = self.image_recognizer.find_thanks_buttons(screenshot)
        logger.debug(f"Found {len(thanks_buttons)} thanks buttons total")
        
        # Step 7: Filter buttons above divider
        buttons_to_click = self.image_recognizer.filter_buttons_above_divider(
            thanks_buttons, divider_y
        )
        buttons_found = len(buttons_to_click)
        logger.info(f"Found {buttons_found} thanks buttons to click")
        
        # Step 8: Find thanked buttons to avoid clicking them
        thanked_buttons = self.image_recognizer.find_thanked_buttons(screenshot)
        thanked_positions = {(btn.x, btn.y) for btn in thanked_buttons}
        
        # Step 9: Click each thanks button (avoiding thanked buttons)
        for button in buttons_to_click:
            # Skip if this position is already thanked
            if (button.x, button.y) in thanked_positions:
                logger.debug(f"Skipping already thanked button at ({button.x}, {button.y})")
                continue
            
            # Click the button
            success = self.auto_clicker.click_button(button, window_offset)
            if success:
                buttons_clicked += 1
                logger.info(f"Clicked thanks button at ({button.x}, {button.y})")
            else:
                logger.warning(f"Failed to click button at ({button.x}, {button.y})")
        
        return (buttons_found, buttons_clicked)

    def refresh_content(self, window_rect: Tuple[int, int, int, int]) -> None:
        """
        通过滚动刷新内容

        Args:
            window_rect: 窗口位置 (left, top, right, bottom)
        """
        left, top, right, bottom = window_rect
        
        # Calculate center of window for scrolling
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        logger.debug(f"Refreshing content at ({center_x}, {center_y})")
        
        # Scroll up first to trigger refresh (like pull-to-refresh)
        self.auto_clicker.scroll_up(center_x, center_y, amount=self.config.scroll_count)
        time.sleep(self.REFRESH_WAIT)
        
        # Then scroll down to load more content
        for _ in range(self.config.scroll_count):
            self.auto_clicker.scroll_down(center_x, center_y, amount=1)
            time.sleep(self.REFRESH_WAIT)

    def get_window_center(
        self, 
        window_rect: Tuple[int, int, int, int]
    ) -> Tuple[int, int]:
        """
        获取窗口中心坐标

        Args:
            window_rect: 窗口位置 (left, top, right, bottom)

        Returns:
            窗口中心坐标 (x, y)
        """
        left, top, right, bottom = window_rect
        return ((left + right) // 2, (top + bottom) // 2)
