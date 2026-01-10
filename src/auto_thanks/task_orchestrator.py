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
        
        # Step 1: Find target window (including minimized windows)
        hwnd = self.window_capture.find_window(include_minimized=True)
        if not hwnd:
            error_msg = f"Target window not found: {self.window_capture.window_title}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Step 2: Wait for window to become visible if minimized/hidden
        if not self.window_capture.is_window_visible():
            logger.info("Window is not visible, waiting for it to become visible...")
            if not self.window_capture.wait_for_visible(
                timeout=self.config.window_visible_timeout
            ):
                error_msg = (
                    f"Timeout waiting for window to become visible "
                    f"after {self.config.window_visible_timeout}s"
                )
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result
        
        # Step 3: Get window position for coordinate calculations
        window_rect = self.window_capture.get_window_rect()
        if not window_rect:
            error_msg = "Failed to get window position"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Step 4: Determine tab processing order based on "+X" indicators
        tabs_to_process = self._get_prioritized_tabs()
        
        # Step 5: Process each tab in priority order
        for tab_name in tabs_to_process:
            try:
                found, clicked, failed = self.process_tab(tab_name, window_rect)
                result.tabs_checked.append(tab_name)
                result.buttons_found += found
                result.buttons_clicked += clicked
                result.failed_clicks += failed
            except Exception as e:
                error_msg = f"Error processing tab '{tab_name}': {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        
        logger.info(
            f"Scan cycle complete: {result.buttons_clicked}/{result.buttons_found} "
            f"buttons clicked ({result.failed_clicks} failed) in {len(result.tabs_checked)} tabs"
        )
        
        return result

    def _get_prioritized_tabs(self) -> List[str]:
        """
        获取按优先级排序的标签列表
        
        优先处理有"+X"指示器的标签

        Returns:
            按优先级排序的标签名称列表
        """
        # Capture screenshot to detect indicators
        screenshot = self.window_capture.capture_screenshot()
        if screenshot is None:
            logger.warning("Failed to capture screenshot for indicator detection, using default order")
            return list(self.DEFAULT_TABS)
        
        # Check which tabs have indicators
        tabs_with_indicators = self.image_recognizer.get_tabs_with_indicators(screenshot)
        
        # Build prioritized list: tabs with indicators first
        prioritized: List[str] = []
        non_prioritized: List[str] = []
        
        for tab_name in self.DEFAULT_TABS:
            if tabs_with_indicators.get(tab_name, False):
                prioritized.append(tab_name)
                logger.info(f"Tab '{tab_name}' has indicator, prioritizing")
            else:
                non_prioritized.append(tab_name)
        
        # Return prioritized tabs first, then the rest
        return prioritized + non_prioritized

    def process_tab(
        self, 
        tab_name: str, 
        window_rect: Tuple[int, int, int, int]
    ) -> Tuple[int, int, int]:
        """
        处理单个标签页

        Args:
            tab_name: 标签名称（"赞" 或 "关注"）
            window_rect: 窗口位置 (left, top, right, bottom)

        Returns:
            (找到的按钮数, 点击的按钮数, 验证失败的点击数)
        """
        logger.info(f"Processing tab: {tab_name}")
        
        window_offset = (window_rect[0], window_rect[1])
        buttons_found = 0
        buttons_clicked = 0
        failed_clicks = 0
        
        # Step 1: Capture screenshot to find tab buttons
        screenshot = self.window_capture.capture_screenshot()
        if screenshot is None:
            logger.error("Failed to capture screenshot for tab detection")
            return (0, 0, 0)
        
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
            return (0, 0, 0)
        
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
        
        # Step 9: Click each thanks button (avoiding thanked buttons) with verification
        for button in buttons_to_click:
            # Skip if this position is already thanked
            if (button.x, button.y) in thanked_positions:
                logger.debug(f"Skipping already thanked button at ({button.x}, {button.y})")
                continue
            
            # Click the button
            success = self.auto_clicker.click_button(button, window_offset)
            if not success:
                logger.warning(f"Failed to click button at ({button.x}, {button.y})")
                continue
            
            # Verify button state changed to "已感谢"
            if self._verify_button_state_changed(button, window_offset):
                buttons_clicked += 1
                logger.info(f"Clicked and verified thanks button at ({button.x}, {button.y})")
            else:
                failed_clicks += 1
                logger.warning(
                    f"Button at ({button.x}, {button.y}) did not change to thanked state, skipping"
                )
        
        return (buttons_found, buttons_clicked, failed_clicks)

    def _verify_button_state_changed(
        self,
        button: MatchResult,
        window_offset: Tuple[int, int]
    ) -> bool:
        """
        验证按钮点击后是否变为"已感谢"状态

        Args:
            button: 被点击的按钮匹配结果
            window_offset: 窗口左上角偏移 (x, y)

        Returns:
            True 如果按钮状态已变为"已感谢"，否则 False
        """
        # Wait for UI to update
        time.sleep(self.config.click_verify_wait)
        
        # Capture new screenshot
        screenshot = self.window_capture.capture_screenshot()
        if screenshot is None:
            logger.error("Failed to capture screenshot for click verification - treating as failed click")
            return False
        
        # Check if a thanked button now exists at or near the clicked position
        thanked_buttons = self.image_recognizer.find_thanked_buttons(screenshot)
        
        # Define tolerance for position matching (buttons may shift slightly)
        tolerance = 10
        
        for thanked in thanked_buttons:
            if (abs(thanked.x - button.x) <= tolerance and 
                abs(thanked.y - button.y) <= tolerance):
                return True
        
        # Also check if the thanks button is no longer there
        thanks_buttons = self.image_recognizer.find_thanks_buttons(screenshot)
        for thanks in thanks_buttons:
            if (abs(thanks.x - button.x) <= tolerance and 
                abs(thanks.y - button.y) <= tolerance):
                # Thanks button still exists at same position - state didn't change
                return False
        
        # Button disappeared but no thanked button found - assume success
        return True

    def refresh_content(self, window_rect: Tuple[int, int, int, int]) -> None:
        """
        通过滚动刷新内容

        Args:
            window_rect: 窗口位置 (left, top, right, bottom)
        """
        # Calculate content area bounds based on tab positions
        content_bounds = self.calculate_content_area(window_rect)
        
        # Get scroll position within content area
        scroll_x, scroll_y = self.get_scroll_position(content_bounds)
        
        logger.debug(f"Refreshing content at ({scroll_x}, {scroll_y}) within content area {content_bounds}")
        
        # Scroll down to trigger refresh and load content (per requirement 5.1)
        for _ in range(self.config.scroll_count):
            self.auto_clicker.scroll_down(scroll_x, scroll_y, amount=1)
            time.sleep(self.REFRESH_WAIT)

    def calculate_content_area(
        self, 
        window_rect: Tuple[int, int, int, int]
    ) -> Tuple[int, int, int, int]:
        """
        根据标签页位置估算内容区域边界

        Args:
            window_rect: 窗口位置 (left, top, right, bottom)

        Returns:
            内容区域边界 (left, top, right, bottom)
        """
        left, top, right, bottom = window_rect
        
        # Try to detect tab buttons to estimate content area top boundary
        screenshot = self.window_capture.capture_screenshot()
        content_top = top
        
        if screenshot is not None:
            tab_buttons = self.image_recognizer.find_tab_buttons(screenshot)
            if tab_buttons:
                # Find the lowest tab button (highest Y value)
                max_tab_y = 0
                max_tab_height = 0
                for tab_match in tab_buttons.values():
                    if tab_match.y > max_tab_y:
                        max_tab_y = tab_match.y
                        max_tab_height = tab_match.height
                
                # Content area starts below the tab buttons
                # Add some padding (tab height + margin)
                content_top = top + max_tab_y + max_tab_height // 2 + 10
                logger.debug(f"Detected tab at y={max_tab_y}, content starts at {content_top}")
        
        # Content area: below tabs, with some margin from window edges
        # Use a small horizontal margin to avoid scrolling at window edges
        margin = 20
        content_left = left + margin
        content_right = right - margin
        content_bottom = bottom - margin
        
        # Ensure content_top is reasonable (at least 1/4 from top of window)
        min_content_top = top + (bottom - top) // 4
        content_top = max(content_top, min_content_top)
        
        return (content_left, content_top, content_right, content_bottom)

    def get_scroll_position(
        self, 
        content_bounds: Tuple[int, int, int, int]
    ) -> Tuple[int, int]:
        """
        获取内容区域内的滚动位置

        Args:
            content_bounds: 内容区域边界 (left, top, right, bottom)

        Returns:
            滚动位置 (x, y)，保证在内容区域内
        """
        left, top, right, bottom = content_bounds
        
        # Calculate center of content area
        scroll_x = (left + right) // 2
        scroll_y = (top + bottom) // 2
        
        # Ensure coordinates are within bounds
        scroll_x = max(left, min(scroll_x, right))
        scroll_y = max(top, min(scroll_y, bottom))
        
        return (scroll_x, scroll_y)

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
