"""Auto Clicker module for simulating mouse operations."""

import time
import logging
from typing import Tuple

import pyautogui

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import MatchResult
except ImportError:
    from auto_thanks.models import MatchResult


logger = logging.getLogger(__name__)


class AutoClicker:
    """自动点击模块，模拟鼠标操作"""
    
    def __init__(self, click_delay: float = 0.5, scroll_amount: int = 3):
        """
        初始化自动点击器
        
        Args:
            click_delay: 点击之间的延迟（秒）
            scroll_amount: 每次滚动的行数
        """
        self.click_delay = click_delay
        self.scroll_amount = scroll_amount
        # Disable pyautogui fail-safe for automation
        pyautogui.FAILSAFE = True
        # Set pause between pyautogui calls
        pyautogui.PAUSE = 0.1
    
    def click_at(self, x: int, y: int) -> bool:
        """
        在指定位置点击
        
        Args:
            x: 屏幕 X 坐标
            y: 屏幕 Y 坐标
            
        Returns:
            点击是否成功
        """
        try:
            pyautogui.click(x, y)
            logger.info(f"Clicked at ({x}, {y})")
            time.sleep(self.click_delay)
            return True
        except Exception as e:
            logger.error(f"Failed to click at ({x}, {y}): {e}")
            return False
    
    def click_button(self, match: MatchResult, window_offset: Tuple[int, int]) -> bool:
        """
        点击匹配到的按钮
        
        Args:
            match: 匹配结果
            window_offset: 窗口左上角偏移 (x, y)
            
        Returns:
            点击是否成功
        """
        # Calculate screen coordinates from match center and window offset
        screen_x = match.x + window_offset[0]
        screen_y = match.y + window_offset[1]
        
        logger.debug(f"Clicking button '{match.template_name}' at screen ({screen_x}, {screen_y})")
        return self.click_at(screen_x, screen_y)
    
    def calculate_click_coordinates(
        self, 
        match: MatchResult, 
        window_offset: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        计算点击的屏幕坐标
        
        Args:
            match: 匹配结果
            window_offset: 窗口左上角偏移 (x, y)
            
        Returns:
            屏幕坐标 (x, y)
        """
        screen_x = match.x + window_offset[0]
        screen_y = match.y + window_offset[1]
        return (screen_x, screen_y)
    
    def scroll_down(self, x: int, y: int, amount: int = None) -> None:
        """
        在指定位置向下滚动
        
        Args:
            x: 滚动位置 X 坐标
            y: 滚动位置 Y 坐标
            amount: 滚动行数（负数表示向下）
        """
        if amount is None:
            amount = self.scroll_amount
        
        try:
            # Move to position first
            pyautogui.moveTo(x, y)
            # Negative scroll = scroll down
            pyautogui.scroll(-amount)
            logger.info(f"Scrolled down {amount} lines at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to scroll down at ({x}, {y}): {e}")
    
    def scroll_up(self, x: int, y: int, amount: int = None) -> None:
        """
        在指定位置向上滚动（用于刷新）
        
        Args:
            x: 滚动位置 X 坐标
            y: 滚动位置 Y 坐标
            amount: 滚动行数（正数表示向上）
        """
        if amount is None:
            amount = self.scroll_amount
        
        try:
            # Move to position first
            pyautogui.moveTo(x, y)
            # Positive scroll = scroll up
            pyautogui.scroll(amount)
            logger.info(f"Scrolled up {amount} lines at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to scroll up at ({x}, {y}): {e}")
    
    def is_within_bounds(
        self, 
        x: int, 
        y: int, 
        bounds: Tuple[int, int, int, int]
    ) -> bool:
        """
        检查坐标是否在窗口边界内
        
        Args:
            x: X 坐标
            y: Y 坐标
            bounds: 窗口边界 (left, top, right, bottom)
            
        Returns:
            是否在边界内
        """
        left, top, right, bottom = bounds
        return left <= x <= right and top <= y <= bottom
