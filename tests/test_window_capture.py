"""Property-based tests for WindowCapture module.

Feature: auto-thanks-clicker
Property 1: Window Finding Correctness
Property 2: Screenshot Dimension Consistency
Validates: Requirements 1.1, 1.2, 1.3
"""

import sys
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st, assume

# Mock win32 modules before importing WindowCapture
mock_win32gui = MagicMock()
mock_win32ui = MagicMock()
mock_win32con = MagicMock()
mock_win32api = MagicMock()

sys.modules['win32gui'] = mock_win32gui
sys.modules['win32ui'] = mock_win32ui
sys.modules['win32con'] = mock_win32con
sys.modules['win32api'] = mock_win32api

# Now import the module - it will use our mocks
import src.auto_thanks.window_capture as window_capture_module
from src.auto_thanks.window_capture import WindowCapture

# Patch the module-level references
window_capture_module.win32gui = mock_win32gui
window_capture_module.win32ui = mock_win32ui
window_capture_module.win32con = mock_win32con
window_capture_module.win32api = mock_win32api


# Strategies for generating test data
window_title_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != "")
hwnd_strategy = st.integers(min_value=1, max_value=2**31 - 1)
coordinate_strategy = st.integers(min_value=0, max_value=4000)


class MockWindowRegistry:
    """Simulates a registry of windows for testing."""
    
    def __init__(self):
        self.windows: Dict[int, Tuple[str, Tuple[int, int, int, int], bool]] = {}
        self._next_hwnd = 1000
    
    def add_window(self, title: str, rect: Tuple[int, int, int, int], visible: bool = True) -> int:
        """Add a window to the registry and return its hwnd."""
        hwnd = self._next_hwnd
        self._next_hwnd += 1
        self.windows[hwnd] = (title, rect, visible)
        return hwnd
    
    def get_title(self, hwnd: int) -> str:
        if hwnd in self.windows:
            return self.windows[hwnd][0]
        return ""
    
    def get_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        if hwnd in self.windows:
            return self.windows[hwnd][1]
        return None
    
    def is_visible(self, hwnd: int) -> bool:
        if hwnd in self.windows:
            return self.windows[hwnd][2]
        return False
    
    def find_by_title(self, title: str) -> List[int]:
        """Find all windows containing the given title."""
        return [hwnd for hwnd, (t, _, v) in self.windows.items() if title in t and v]


def setup_mock_win32(registry: MockWindowRegistry):
    """Configure win32gui mocks to use the registry."""
    
    def mock_enum_windows(callback, results):
        for hwnd in registry.windows.keys():
            callback(hwnd, results)
        return True
    
    def mock_get_window_text(hwnd):
        return registry.get_title(hwnd)
    
    def mock_is_window_visible(hwnd):
        return registry.is_visible(hwnd)
    
    def mock_get_window_rect(hwnd):
        rect = registry.get_rect(hwnd)
        if rect is None:
            raise Exception("Invalid window handle")
        return rect
    
    def mock_find_window(class_name, title):
        matches = registry.find_by_title(title) if title else []
        return matches[0] if matches else 0
    
    def mock_is_iconic(hwnd):
        return False
    
    mock_win32gui.EnumWindows = mock_enum_windows
    mock_win32gui.GetWindowText = mock_get_window_text
    mock_win32gui.IsWindowVisible = mock_is_window_visible
    mock_win32gui.GetWindowRect = mock_get_window_rect
    mock_win32gui.FindWindow = mock_find_window
    mock_win32gui.IsIconic = mock_is_iconic



@given(
    window_title=window_title_strategy,
    left=coordinate_strategy,
    top=coordinate_strategy,
    width=st.integers(min_value=100, max_value=2000),
    height=st.integers(min_value=100, max_value=2000),
)
@settings(max_examples=100)
def test_property_1_window_finding_correctness(
    window_title: str, left: int, top: int, width: int, height: int
):
    """
    Feature: auto-thanks-clicker
    Property 1: Window Finding Correctness
    Validates: Requirements 1.1, 1.3
    
    For any window title string that matches an existing window, the find_window 
    function SHALL return a valid window handle (non-None integer). For any window 
    title that does not match any existing window, the function SHALL return None.
    """
    registry = MockWindowRegistry()
    rect = (left, top, left + width, top + height)
    
    # Add the target window
    expected_hwnd = registry.add_window(window_title, rect, visible=True)
    
    # Add some other windows that shouldn't match
    registry.add_window("Other Window 1", (0, 0, 100, 100), visible=True)
    registry.add_window("Different App", (200, 200, 400, 400), visible=True)
    
    setup_mock_win32(registry)
    
    # Test: Window with matching title should be found
    capture = WindowCapture(window_title)
    found_hwnd = capture.find_window()
    
    assert found_hwnd is not None, f"Should find window with title '{window_title}'"
    assert isinstance(found_hwnd, int), "HWND should be an integer"
    assert found_hwnd == expected_hwnd, f"Should return correct hwnd {expected_hwnd}"
    
    # Test: Window with non-matching title should not be found
    capture_nonexistent = WindowCapture("NonExistentWindowTitle12345XYZ")
    found_hwnd_none = capture_nonexistent.find_window()
    
    assert found_hwnd_none is None, "Should return None for non-existent window"


@given(
    window_title=window_title_strategy,
    left=coordinate_strategy,
    top=coordinate_strategy,
    width=st.integers(min_value=100, max_value=2000),
    height=st.integers(min_value=100, max_value=2000),
)
@settings(max_examples=100)
def test_property_2_screenshot_dimension_consistency(
    window_title: str, left: int, top: int, width: int, height: int
):
    """
    Feature: auto-thanks-clicker
    Property 2: Screenshot Dimension Consistency
    Validates: Requirements 1.2
    
    For any valid window handle, the captured screenshot dimensions (width, height) 
    SHALL match the window's dimensions as reported by get_window_rect.
    """
    registry = MockWindowRegistry()
    rect = (left, top, left + width, top + height)
    hwnd = registry.add_window(window_title, rect, visible=True)
    
    setup_mock_win32(registry)
    
    # Create mock for screenshot capture
    def create_mock_bitmap(w, h):
        """Create a mock bitmap that returns correct dimensions."""
        mock_bitmap = MagicMock()
        mock_bitmap.GetInfo.return_value = {
            'bmWidth': w,
            'bmHeight': h,
        }
        # Create fake image data (BGRA format)
        fake_data = np.zeros((h, w, 4), dtype=np.uint8).tobytes()
        mock_bitmap.GetBitmapBits.return_value = fake_data
        mock_bitmap.GetHandle.return_value = 1
        return mock_bitmap
    
    # Setup additional mocks for screenshot
    mock_dc = MagicMock()
    mock_save_dc = MagicMock()
    mock_bitmap = create_mock_bitmap(width, height)
    
    mock_win32gui.GetWindowDC.return_value = 1
    mock_win32gui.DeleteObject.return_value = None
    mock_win32gui.ReleaseDC.return_value = None
    mock_win32gui.GetClientRect.return_value = (0, 0, width, height)
    mock_win32gui.ClientToScreen.return_value = (left, top)
    
    mock_win32ui.CreateDCFromHandle.return_value = mock_dc
    mock_dc.CreateCompatibleDC.return_value = mock_save_dc
    mock_win32ui.CreateBitmap.return_value = mock_bitmap
    mock_save_dc.GetSafeHdc.return_value = 1
    
    # Mock windll for PrintWindow
    with patch.object(window_capture_module, 'windll') as mock_windll:
        mock_windll.user32.PrintWindow.return_value = 1
        
        capture = WindowCapture(window_title)
        capture.find_window()
        
        # Get window rect
        window_rect = capture.get_window_rect()
        assert window_rect is not None, "Should get window rect"
        
        rect_width = window_rect[2] - window_rect[0]
        rect_height = window_rect[3] - window_rect[1]
        
        # Capture screenshot
        screenshot = capture.capture_screenshot()
        
        assert screenshot is not None, "Should capture screenshot"
        assert isinstance(screenshot, np.ndarray), "Screenshot should be numpy array"
        
        # Verify dimensions match
        screenshot_height, screenshot_width = screenshot.shape[:2]
        
        assert screenshot_width == rect_width, \
            f"Screenshot width {screenshot_width} should match window width {rect_width}"
        assert screenshot_height == rect_height, \
            f"Screenshot height {screenshot_height} should match window height {rect_height}"



def test_find_window_returns_none_when_no_windows():
    """Test that find_window returns None when no matching windows exist."""
    registry = MockWindowRegistry()
    setup_mock_win32(registry)
    
    capture = WindowCapture("NonExistentWindow")
    result = capture.find_window()
    
    assert result is None


def test_is_window_visible_returns_false_for_hidden_window():
    """Test that is_window_visible returns False for hidden windows."""
    registry = MockWindowRegistry()
    registry.add_window("Hidden Window", (0, 0, 100, 100), visible=False)
    setup_mock_win32(registry)
    
    capture = WindowCapture("Hidden Window")
    # Window won't be found because it's not visible
    assert capture.is_window_visible() is False


def test_get_window_rect_returns_none_without_finding_window():
    """Test that get_window_rect returns None if window not found."""
    registry = MockWindowRegistry()
    setup_mock_win32(registry)
    
    capture = WindowCapture("NonExistentWindow")
    result = capture.get_window_rect()
    
    assert result is None


def test_partial_title_match():
    """Test that partial window title matching works."""
    registry = MockWindowRegistry()
    hwnd = registry.add_window("My Application - Document.txt", (0, 0, 800, 600), visible=True)
    setup_mock_win32(registry)
    
    # Should find window with partial match
    capture = WindowCapture("My Application")
    found = capture.find_window()
    
    assert found == hwnd


def test_reset_clears_hwnd():
    """Test that reset() clears the cached window handle."""
    registry = MockWindowRegistry()
    registry.add_window("Test Window", (0, 0, 100, 100), visible=True)
    setup_mock_win32(registry)
    
    capture = WindowCapture("Test Window")
    capture.find_window()
    
    assert capture.hwnd is not None
    
    capture.reset()
    
    assert capture.hwnd is None
