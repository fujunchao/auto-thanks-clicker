"""Window capture module for locating and capturing screenshots of target windows."""

import logging
from typing import Optional, Tuple, List

import numpy as np

try:
    import win32gui
    import win32ui
    import win32con
    import win32api
    import win32process
    import psutil
    from ctypes import windll
except ImportError:
    # Allow module to be imported on non-Windows for testing
    win32gui = None
    win32ui = None
    win32con = None
    win32api = None
    win32process = None
    psutil = None
    windll = None

logger = logging.getLogger(__name__)


class WindowCapture:
    """窗口捕获模块，负责定位和截图目标窗口"""

    def __init__(self, window_title: str = "", process_name: str = ""):
        """
        初始化窗口捕获器

        Args:
            window_title: 目标窗口标题（支持部分匹配）
            process_name: 目标进程名（支持部分匹配，如 "notepad.exe"）
        """
        self.window_title = window_title
        self.process_name = process_name
        self._hwnd: Optional[int] = None

    def find_window_by_process(self, include_minimized: bool = True) -> Optional[int]:
        """
        通过进程名查找窗口

        Args:
            include_minimized: 是否包含最小化窗口（默认True）

        Returns:
            窗口句柄 (HWND)，未找到返回 None
        """
        if win32gui is None or win32process is None or psutil is None:
            logger.error("win32gui/win32process/psutil not available - Windows only feature")
            return None

        if not self.process_name:
            return None

        def enum_callback(hwnd: int, results: list) -> bool:
            """枚举窗口回调函数"""
            try:
                # Get process ID for this window
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                # Get process name
                try:
                    process = psutil.Process(pid)
                    proc_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return True
                
                # Check if process name matches (case-insensitive partial match)
                if self.process_name.lower() in proc_name.lower():
                    # Check visibility based on include_minimized flag
                    if include_minimized:
                        if win32gui.IsWindow(hwnd):
                            # Only include windows with a title (main windows)
                            if win32gui.GetWindowText(hwnd):
                                results.append(hwnd)
                    else:
                        if win32gui.IsWindowVisible(hwnd):
                            if win32gui.GetWindowText(hwnd):
                                results.append(hwnd)
            except Exception as e:
                logger.debug(f"Error checking window {hwnd}: {e}")
            return True

        results: list = []
        try:
            win32gui.EnumWindows(enum_callback, results)
        except Exception as e:
            logger.error(f"Error enumerating windows by process: {e}")
            return None

        if results:
            self._hwnd = results[0]
            logger.info(f"Found window by process: {self.process_name} (hwnd={self._hwnd})")
            return self._hwnd

        logger.warning(f"Window not found for process: {self.process_name}")
        return None

    def find_window(self, include_minimized: bool = True) -> Optional[int]:
        """
        查找目标窗口（支持标题或进程名匹配）

        Args:
            include_minimized: 是否包含最小化窗口（默认True）

        Returns:
            窗口句柄 (HWND)，未找到返回 None
        """
        if win32gui is None:
            logger.error("win32gui not available - Windows only feature")
            return None

        # First try to find by window title if provided
        if self.window_title:
            def enum_callback(hwnd: int, results: list) -> bool:
                """枚举窗口回调函数"""
                title = win32gui.GetWindowText(hwnd)
                if self.window_title and self.window_title in title:
                    # Check visibility based on include_minimized flag
                    if include_minimized:
                        # Include window if it exists (even if minimized)
                        # IsWindow checks if handle is valid
                        if win32gui.IsWindow(hwnd):
                            results.append(hwnd)
                    else:
                        # Only include visible, non-minimized windows
                        if win32gui.IsWindowVisible(hwnd):
                            results.append(hwnd)
                return True

            results: list = []
            try:
                win32gui.EnumWindows(enum_callback, results)
            except Exception as e:
                logger.error(f"Error enumerating windows: {e}")
                # Don't return yet, try process name matching

            if results:
                self._hwnd = results[0]
                logger.info(f"Found window by title: {self.window_title} (hwnd={self._hwnd})")
                return self._hwnd

            # Try exact match with FindWindow
            try:
                hwnd = win32gui.FindWindow(None, self.window_title)
                if hwnd:
                    self._hwnd = hwnd
                    logger.info(f"Found window (exact match): {self.window_title} (hwnd={self._hwnd})")
                    return self._hwnd
            except Exception as e:
                logger.error(f"Error finding window: {e}")

        # If title matching failed or no title provided, try process name matching
        if self.process_name:
            result = self.find_window_by_process(include_minimized)
            if result:
                return result

        # Log appropriate warning
        if self.window_title and self.process_name:
            logger.warning(f"Window not found by title '{self.window_title}' or process '{self.process_name}'")
        elif self.window_title:
            logger.warning(f"Window not found: {self.window_title}")
        elif self.process_name:
            logger.warning(f"Window not found for process: {self.process_name}")
        else:
            logger.warning("No window title or process name specified")
        
        return None

    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口位置和大小

        Returns:
            (left, top, right, bottom) 元组，窗口不存在返回 None
        """
        if win32gui is None:
            logger.error("win32gui not available - Windows only feature")
            return None

        hwnd = self._hwnd or self.find_window()
        if not hwnd:
            return None

        try:
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            logger.error(f"Error getting window rect: {e}")
            return None

    def get_client_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口客户区位置和大小

        Returns:
            (left, top, right, bottom) 元组，窗口不存在返回 None
        """
        if win32gui is None:
            logger.error("win32gui not available - Windows only feature")
            return None

        hwnd = self._hwnd or self.find_window()
        if not hwnd:
            return None

        try:
            # Get client rect (relative to window)
            client_rect = win32gui.GetClientRect(hwnd)
            # Convert client coordinates to screen coordinates
            left, top = win32gui.ClientToScreen(hwnd, (0, 0))
            right = left + client_rect[2]
            bottom = top + client_rect[3]
            return (left, top, right, bottom)
        except Exception as e:
            logger.error(f"Error getting client rect: {e}")
            return None

    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        捕获窗口截图

        Returns:
            OpenCV 格式的图像数组 (BGR)，失败返回 None
        """
        if win32gui is None or win32ui is None:
            logger.error("win32gui/win32ui not available - Windows only feature")
            return None

        hwnd = self._hwnd or self.find_window()
        if not hwnd:
            logger.error("Cannot capture screenshot: window not found")
            return None

        if not self.is_window_visible():
            logger.warning("Window is not visible, cannot capture screenshot")
            return None

        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                logger.error(f"Invalid window dimensions: {width}x{height}")
                return None

            # Get window device context
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # Use PrintWindow for better compatibility with layered windows
            result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)

            if result == 0:
                # Fallback to BitBlt if PrintWindow fails
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

            # Convert to numpy array
            bmp_info = bitmap.GetInfo()
            bmp_str = bitmap.GetBitmapBits(True)

            img = np.frombuffer(bmp_str, dtype=np.uint8)
            img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

            # Convert BGRA to BGR
            img = img[:, :, :3]

            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            logger.debug(f"Captured screenshot: {width}x{height}")
            return img

        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None

    def is_window_visible(self) -> bool:
        """检查窗口是否可见"""
        if win32gui is None:
            return False

        hwnd = self._hwnd or self.find_window()
        if not hwnd:
            return False

        try:
            # Check if window is visible and not minimized
            if not win32gui.IsWindowVisible(hwnd):
                return False

            # Check if window is minimized (iconic)
            if win32gui.IsIconic(hwnd):
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking window visibility: {e}")
            return False

    def bring_to_front(self) -> bool:
        """将窗口置于前台"""
        if win32gui is None:
            return False

        hwnd = self._hwnd or self.find_window()
        if not hwnd:
            logger.error("Cannot bring window to front: window not found")
            return False

        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"Brought window to front: hwnd={hwnd}")
            return True
        except Exception as e:
            logger.error(f"Error bringing window to front: {e}")
            return False

    @property
    def hwnd(self) -> Optional[int]:
        """获取当前窗口句柄"""
        return self._hwnd

    def reset(self) -> None:
        """重置窗口句柄，强制下次重新查找"""
        self._hwnd = None

    def wait_for_visible(self, timeout: float = 30.0, poll_interval: float = 0.5) -> bool:
        """
        等待窗口变为可见状态

        Args:
            timeout: 超时时间（秒），默认30秒
            poll_interval: 轮询间隔（秒），默认0.5秒

        Returns:
            True 如果窗口在超时前变为可见，否则 False
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # First ensure we have a window handle
            hwnd = self._hwnd or self.find_window(include_minimized=True)
            if not hwnd:
                logger.debug("Window not found, waiting...")
                time.sleep(poll_interval)
                continue
            
            # Check if window is visible
            if self.is_window_visible():
                logger.info(f"Window is now visible (hwnd={hwnd})")
                return True
            
            logger.debug(f"Window not visible yet, waiting... (elapsed: {time.time() - start_time:.1f}s)")
            time.sleep(poll_interval)
        
        logger.error(f"Timeout waiting for window to become visible after {timeout}s")
        return False
