"""Unit tests for TaskOrchestrator module.

Feature: auto-thanks-clicker
Tests: Scan flow logic, tab switching logic
Validates: Requirements 2.2, 2.3, 4.1, 4.3
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import numpy as np

from src.auto_thanks.task_orchestrator import TaskOrchestrator
from src.auto_thanks.models import Config, MatchResult, ScanResult
from src.auto_thanks.window_capture import WindowCapture
from src.auto_thanks.image_recognizer import ImageRecognizer
from src.auto_thanks.auto_clicker import AutoClicker


@pytest.fixture
def mock_config():
    """Create a test configuration."""
    return Config(
        window_title="Test Window",
        check_interval=60,
        scroll_count=2,
        click_delay=0.1,
        confidence_threshold=0.8,
        templates_dir="templates",
        log_file="test.log"
    )


@pytest.fixture
def mock_window_capture():
    """Create a mock WindowCapture."""
    mock = Mock(spec=WindowCapture)
    mock.window_title = "Test Window"
    return mock


@pytest.fixture
def mock_image_recognizer():
    """Create a mock ImageRecognizer."""
    return Mock(spec=ImageRecognizer)


@pytest.fixture
def mock_auto_clicker():
    """Create a mock AutoClicker."""
    mock = Mock(spec=AutoClicker)
    mock.click_button.return_value = True
    return mock


@pytest.fixture
def orchestrator(mock_window_capture, mock_image_recognizer, mock_auto_clicker, mock_config):
    """Create a TaskOrchestrator with mocked dependencies."""
    return TaskOrchestrator(
        window_capture=mock_window_capture,
        image_recognizer=mock_image_recognizer,
        auto_clicker=mock_auto_clicker,
        config=mock_config
    )


@pytest.fixture
def sample_screenshot():
    """Create a sample screenshot array."""
    return np.zeros((600, 800, 3), dtype=np.uint8)


@pytest.fixture
def sample_match_result():
    """Create a sample MatchResult."""
    return MatchResult(
        x=100, y=200, width=50, height=25,
        confidence=0.95, template_name="thanks_button.png"
    )


class TestTaskOrchestratorInitialization:
    """Tests for TaskOrchestrator initialization."""

    def test_initialization(self, mock_window_capture, mock_image_recognizer, 
                           mock_auto_clicker, mock_config):
        """Test TaskOrchestrator initializes with correct dependencies."""
        orchestrator = TaskOrchestrator(
            window_capture=mock_window_capture,
            image_recognizer=mock_image_recognizer,
            auto_clicker=mock_auto_clicker,
            config=mock_config
        )
        
        assert orchestrator.window_capture is mock_window_capture
        assert orchestrator.image_recognizer is mock_image_recognizer
        assert orchestrator.auto_clicker is mock_auto_clicker
        assert orchestrator.config is mock_config

    def test_default_tabs(self, orchestrator):
        """Test default tabs are configured correctly."""
        assert "赞" in orchestrator.DEFAULT_TABS
        assert "关注" in orchestrator.DEFAULT_TABS


class TestRunScanCycle:
    """Tests for run_scan_cycle method."""

    def test_scan_cycle_window_not_found(self, orchestrator, mock_window_capture):
        """Test scan cycle handles window not found error.
        
        Validates: Requirements 2.2 - Window must be found before scanning
        """
        mock_window_capture.find_window.return_value = None
        
        result = orchestrator.run_scan_cycle()
        
        assert isinstance(result, ScanResult)
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()
        assert result.buttons_found == 0
        assert result.buttons_clicked == 0

    def test_scan_cycle_window_not_visible(self, orchestrator, mock_window_capture):
        """Test scan cycle handles hidden/minimized window.
        
        Validates: Requirements 2.2 - Window must be visible
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = False
        
        result = orchestrator.run_scan_cycle()
        
        assert len(result.errors) > 0
        assert "not visible" in result.errors[0].lower()

    def test_scan_cycle_window_rect_failure(self, orchestrator, mock_window_capture):
        """Test scan cycle handles window rect retrieval failure."""
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = None
        
        result = orchestrator.run_scan_cycle()
        
        assert len(result.errors) > 0
        assert "position" in result.errors[0].lower()

    @patch.object(TaskOrchestrator, 'process_tab')
    def test_scan_cycle_processes_all_tabs(self, mock_process_tab, orchestrator, 
                                           mock_window_capture):
        """Test scan cycle processes all configured tabs.
        
        Validates: Requirements 2.2, 2.3 - Both tabs should be checked
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_process_tab.return_value = (2, 1)
        
        result = orchestrator.run_scan_cycle()
        
        assert mock_process_tab.call_count == len(orchestrator.DEFAULT_TABS)
        assert "赞" in result.tabs_checked
        assert "关注" in result.tabs_checked

    @patch.object(TaskOrchestrator, 'process_tab')
    def test_scan_cycle_aggregates_results(self, mock_process_tab, orchestrator,
                                           mock_window_capture):
        """Test scan cycle correctly aggregates results from all tabs."""
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_process_tab.side_effect = [(3, 2), (2, 1)]  # Different results per tab
        
        result = orchestrator.run_scan_cycle()
        
        assert result.buttons_found == 5  # 3 + 2
        assert result.buttons_clicked == 3  # 2 + 1

    @patch.object(TaskOrchestrator, 'process_tab')
    def test_scan_cycle_handles_tab_error(self, mock_process_tab, orchestrator,
                                          mock_window_capture):
        """Test scan cycle continues after tab processing error."""
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_process_tab.side_effect = [Exception("Tab error"), (2, 1)]
        
        result = orchestrator.run_scan_cycle()
        
        # Should have one error but still process second tab
        assert len(result.errors) == 1
        assert result.buttons_found == 2
        assert result.buttons_clicked == 1


class TestProcessTab:
    """Tests for process_tab method."""

    def test_process_tab_screenshot_failure(self, orchestrator, mock_window_capture):
        """Test process_tab handles screenshot failure."""
        mock_window_capture.capture_screenshot.return_value = None
        window_rect = (0, 0, 800, 600)
        
        found, clicked = orchestrator.process_tab("赞", window_rect)
        
        assert found == 0
        assert clicked == 0

    @patch('time.sleep')
    def test_process_tab_clicks_tab_button(self, mock_sleep, orchestrator, 
                                           mock_window_capture, mock_image_recognizer,
                                           mock_auto_clicker, sample_screenshot):
        """Test process_tab clicks the correct tab button.
        
        Validates: Requirements 2.3 - Tab should be clicked to switch views
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        tab_match = MatchResult(x=50, y=30, width=40, height=20, 
                               confidence=0.9, template_name="tab_likes.png")
        mock_image_recognizer.find_tab_buttons.return_value = {"赞": tab_match}
        mock_image_recognizer.find_thanks_buttons.return_value = []
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_divider_line.return_value = None
        mock_image_recognizer.filter_buttons_above_divider.return_value = []
        
        window_rect = (100, 100, 900, 700)
        orchestrator.process_tab("赞", window_rect)
        
        # Verify tab button was clicked
        mock_auto_clicker.click_button.assert_called()
        call_args = mock_auto_clicker.click_button.call_args_list[0]
        assert call_args[0][0] == tab_match

    @patch('time.sleep')
    def test_process_tab_finds_and_clicks_thanks_buttons(self, mock_sleep, orchestrator,
                                                         mock_window_capture, 
                                                         mock_image_recognizer,
                                                         mock_auto_clicker,
                                                         sample_screenshot):
        """Test process_tab finds and clicks thanks buttons.
        
        Validates: Requirements 4.1 - Thanks buttons should be clicked
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        thanks_buttons = [
            MatchResult(x=100, y=200, width=50, height=25, 
                       confidence=0.95, template_name="thanks_button.png"),
            MatchResult(x=100, y=300, width=50, height=25,
                       confidence=0.92, template_name="thanks_button.png")
        ]
        mock_image_recognizer.find_thanks_buttons.return_value = thanks_buttons
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_divider_line.return_value = 400
        mock_image_recognizer.filter_buttons_above_divider.return_value = thanks_buttons
        
        window_rect = (0, 0, 800, 600)
        found, clicked = orchestrator.process_tab("赞", window_rect)
        
        assert found == 2
        assert clicked == 2

    @patch('time.sleep')
    def test_process_tab_skips_thanked_buttons(self, mock_sleep, orchestrator,
                                               mock_window_capture,
                                               mock_image_recognizer,
                                               mock_auto_clicker,
                                               sample_screenshot):
        """Test process_tab does not click already thanked buttons.
        
        Validates: Requirements 4.3 - Thanked buttons should not be clicked
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        # One thanks button at same position as a thanked button
        thanks_button = MatchResult(x=100, y=200, width=50, height=25,
                                   confidence=0.95, template_name="thanks_button.png")
        thanked_button = MatchResult(x=100, y=200, width=50, height=25,
                                    confidence=0.95, template_name="thanked_button.png")
        
        mock_image_recognizer.find_thanks_buttons.return_value = [thanks_button]
        mock_image_recognizer.find_thanked_buttons.return_value = [thanked_button]
        mock_image_recognizer.find_divider_line.return_value = None
        mock_image_recognizer.filter_buttons_above_divider.return_value = [thanks_button]
        
        window_rect = (0, 0, 800, 600)
        found, clicked = orchestrator.process_tab("赞", window_rect)
        
        # Button found but not clicked (already thanked)
        assert found == 1
        assert clicked == 0

    @patch('time.sleep')
    def test_process_tab_respects_divider_line(self, mock_sleep, orchestrator,
                                               mock_window_capture,
                                               mock_image_recognizer,
                                               mock_auto_clicker,
                                               sample_screenshot):
        """Test process_tab only clicks buttons above divider line.
        
        Validates: Requirements 2.4 - Only buttons above divider should be clicked
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        all_buttons = [
            MatchResult(x=100, y=200, width=50, height=25,
                       confidence=0.95, template_name="thanks_button.png"),
            MatchResult(x=100, y=500, width=50, height=25,
                       confidence=0.92, template_name="thanks_button.png")
        ]
        buttons_above = [all_buttons[0]]  # Only first button above divider
        
        mock_image_recognizer.find_thanks_buttons.return_value = all_buttons
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_divider_line.return_value = 400
        mock_image_recognizer.filter_buttons_above_divider.return_value = buttons_above
        
        window_rect = (0, 0, 800, 600)
        found, clicked = orchestrator.process_tab("赞", window_rect)
        
        # Only button above divider should be counted
        assert found == 1
        assert clicked == 1


class TestRefreshContent:
    """Tests for refresh_content method."""

    @patch('time.sleep')
    def test_refresh_content_scrolls_at_window_center(self, mock_sleep, orchestrator,
                                                      mock_auto_clicker, mock_config):
        """Test refresh_content scrolls at window center."""
        window_rect = (100, 100, 900, 700)
        expected_center_x = (100 + 900) // 2  # 500
        expected_center_y = (100 + 700) // 2  # 400
        
        orchestrator.refresh_content(window_rect)
        
        # Verify scroll_up was called at center
        mock_auto_clicker.scroll_up.assert_called()
        call_args = mock_auto_clicker.scroll_up.call_args
        assert call_args[0][0] == expected_center_x
        assert call_args[0][1] == expected_center_y

    @patch('time.sleep')
    def test_refresh_content_scrolls_configured_times(self, mock_sleep, orchestrator,
                                                      mock_auto_clicker, mock_config):
        """Test refresh_content scrolls the configured number of times."""
        window_rect = (0, 0, 800, 600)
        
        orchestrator.refresh_content(window_rect)
        
        # Should scroll down scroll_count times
        assert mock_auto_clicker.scroll_down.call_count == mock_config.scroll_count


class TestGetWindowCenter:
    """Tests for get_window_center method."""

    def test_get_window_center_calculation(self, orchestrator):
        """Test window center calculation."""
        window_rect = (100, 200, 500, 600)
        
        center = orchestrator.get_window_center(window_rect)
        
        assert center == (300, 400)  # (100+500)/2, (200+600)/2

    def test_get_window_center_zero_origin(self, orchestrator):
        """Test window center with zero origin."""
        window_rect = (0, 0, 800, 600)
        
        center = orchestrator.get_window_center(window_rect)
        
        assert center == (400, 300)
