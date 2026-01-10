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
        log_file="test.log",
        click_verify_wait=0.3,
        window_visible_timeout=30.0
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
        """Test scan cycle handles hidden/minimized window by waiting.
        
        Validates: Requirements 1.4 - Wait for window to become visible
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = False
        mock_window_capture.wait_for_visible.return_value = False  # Timeout
        
        result = orchestrator.run_scan_cycle()
        
        # Should have called wait_for_visible
        mock_window_capture.wait_for_visible.assert_called_once()
        assert len(result.errors) > 0
        assert "timeout" in result.errors[0].lower()

    def test_scan_cycle_window_becomes_visible(self, orchestrator, mock_window_capture):
        """Test scan cycle proceeds when window becomes visible.
        
        Validates: Requirements 1.4 - Continue after window becomes visible
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = False
        mock_window_capture.wait_for_visible.return_value = True  # Window became visible
        mock_window_capture.get_window_rect.return_value = None  # Fail at next step for simplicity
        
        result = orchestrator.run_scan_cycle()
        
        # Should have called wait_for_visible and proceeded
        mock_window_capture.wait_for_visible.assert_called_once()
        # Error should be about window position, not visibility
        assert len(result.errors) > 0
        assert "position" in result.errors[0].lower()

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
        mock_process_tab.return_value = (2, 1, 0)  # (found, clicked, failed)
        
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
        mock_process_tab.side_effect = [(3, 2, 0), (2, 1, 1)]  # Different results per tab
        
        result = orchestrator.run_scan_cycle()
        
        assert result.buttons_found == 5  # 3 + 2
        assert result.buttons_clicked == 3  # 2 + 1
        assert result.failed_clicks == 1  # 0 + 1

    @patch.object(TaskOrchestrator, 'process_tab')
    def test_scan_cycle_handles_tab_error(self, mock_process_tab, orchestrator,
                                          mock_window_capture):
        """Test scan cycle continues after tab processing error."""
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_process_tab.side_effect = [Exception("Tab error"), (2, 1, 0)]
        
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
        
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        assert found == 0
        assert clicked == 0
        assert failed == 0

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
        thanked_buttons = [
            MatchResult(x=100, y=200, width=50, height=25,
                       confidence=0.95, template_name="thanked_button.png"),
            MatchResult(x=100, y=300, width=50, height=25,
                       confidence=0.92, template_name="thanked_button.png")
        ]
        mock_image_recognizer.find_thanks_buttons.return_value = thanks_buttons
        # First call returns empty (initial), subsequent calls return thanked (after click)
        mock_image_recognizer.find_thanked_buttons.side_effect = [
            [],  # Initial check
            thanked_buttons,  # After first click verification
            thanked_buttons,  # After second click verification
        ]
        mock_image_recognizer.find_divider_line.return_value = 400
        mock_image_recognizer.filter_buttons_above_divider.return_value = thanks_buttons
        
        window_rect = (0, 0, 800, 600)
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        assert found == 2
        assert clicked == 2
        assert failed == 0

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
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        # Button found but not clicked (already thanked)
        assert found == 1
        assert clicked == 0
        assert failed == 0

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
        thanked_button = MatchResult(x=100, y=200, width=50, height=25,
                                    confidence=0.95, template_name="thanked_button.png")
        
        mock_image_recognizer.find_thanks_buttons.return_value = all_buttons
        # First call returns empty (initial), subsequent call returns thanked (after click)
        mock_image_recognizer.find_thanked_buttons.side_effect = [
            [],  # Initial check
            [thanked_button],  # After click verification
        ]
        mock_image_recognizer.find_divider_line.return_value = 400
        mock_image_recognizer.filter_buttons_above_divider.return_value = buttons_above
        
        window_rect = (0, 0, 800, 600)
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        # Only button above divider should be counted
        assert found == 1
        assert clicked == 1
        assert failed == 0


class TestRefreshContent:
    """Tests for refresh_content method."""

    @patch('time.sleep')
    def test_refresh_content_scrolls_at_content_center(self, mock_sleep, orchestrator,
                                                       mock_window_capture,
                                                       mock_image_recognizer,
                                                       mock_auto_clicker, mock_config,
                                                       sample_screenshot):
        """Test refresh_content scrolls at content area center."""
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        window_rect = (100, 100, 900, 700)
        
        orchestrator.refresh_content(window_rect)
        
        # Verify scroll_down was called within content area (no scroll_up per requirement 5.1)
        mock_auto_clicker.scroll_down.assert_called()
        call_args = mock_auto_clicker.scroll_down.call_args
        scroll_x, scroll_y = call_args[0][0], call_args[0][1]
        
        # Scroll should be within content bounds (with margins)
        assert 120 <= scroll_x <= 880  # 100+20 to 900-20
        assert scroll_y >= 250  # At least 1/4 from top (100 + 150)

    @patch('time.sleep')
    def test_refresh_content_scrolls_configured_times(self, mock_sleep, orchestrator,
                                                      mock_window_capture,
                                                      mock_image_recognizer,
                                                      mock_auto_clicker, mock_config,
                                                      sample_screenshot):
        """Test refresh_content scrolls the configured number of times."""
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
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


class TestVerifyButtonStateChanged:
    """Tests for _verify_button_state_changed method.
    
    Validates: Requirements 4.2, 4.5
    """

    @patch('time.sleep')
    def test_verify_state_changed_success(self, mock_sleep, orchestrator,
                                          mock_window_capture,
                                          mock_image_recognizer,
                                          sample_screenshot):
        """Test verification succeeds when thanked button appears at same position.
        
        Validates: Requirements 4.2 - Button should change to thanked state
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        # Original button position
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        # Thanked button appears at same position
        thanked_button = MatchResult(x=100, y=200, width=50, height=25,
                                    confidence=0.95, template_name="thanked_button.png")
        mock_image_recognizer.find_thanked_buttons.return_value = [thanked_button]
        mock_image_recognizer.find_thanks_buttons.return_value = []
        
        result = orchestrator._verify_button_state_changed(button, (0, 0))
        
        assert result is True

    @patch('time.sleep')
    def test_verify_state_changed_with_tolerance(self, mock_sleep, orchestrator,
                                                  mock_window_capture,
                                                  mock_image_recognizer,
                                                  sample_screenshot):
        """Test verification succeeds when thanked button is within tolerance.
        
        Validates: Requirements 4.2 - Allow slight position shift
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        # Thanked button slightly shifted (within tolerance of 10)
        thanked_button = MatchResult(x=105, y=198, width=50, height=25,
                                    confidence=0.95, template_name="thanked_button.png")
        mock_image_recognizer.find_thanked_buttons.return_value = [thanked_button]
        mock_image_recognizer.find_thanks_buttons.return_value = []
        
        result = orchestrator._verify_button_state_changed(button, (0, 0))
        
        assert result is True

    @patch('time.sleep')
    def test_verify_state_not_changed(self, mock_sleep, orchestrator,
                                      mock_window_capture,
                                      mock_image_recognizer,
                                      sample_screenshot):
        """Test verification fails when thanks button still exists.
        
        Validates: Requirements 4.5 - Log warning when state doesn't change
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        # Thanks button still at same position (not changed)
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_thanks_buttons.return_value = [button]
        
        result = orchestrator._verify_button_state_changed(button, (0, 0))
        
        assert result is False

    @patch('time.sleep')
    def test_verify_state_button_disappeared(self, mock_sleep, orchestrator,
                                             mock_window_capture,
                                             mock_image_recognizer,
                                             sample_screenshot):
        """Test verification succeeds when button disappears (assumed success).
        
        Validates: Requirements 4.2 - Button no longer visible means success
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        # No buttons found at all
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_thanks_buttons.return_value = []
        
        result = orchestrator._verify_button_state_changed(button, (0, 0))
        
        assert result is True

    @patch('time.sleep')
    def test_verify_state_screenshot_failure(self, mock_sleep, orchestrator,
                                             mock_window_capture):
        """Test verification returns False on screenshot failure (treated as failed click).
        
        Validates: Requirements 4.2, 4.5 - Screenshot failure should be treated as failed click
        """
        mock_window_capture.capture_screenshot.return_value = None
        
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        result = orchestrator._verify_button_state_changed(button, (0, 0))
        
        # Should return False to count as failed click
        assert result is False

    @patch('time.sleep')
    def test_verify_uses_config_wait_time(self, mock_sleep, orchestrator,
                                          mock_window_capture,
                                          mock_image_recognizer,
                                          sample_screenshot,
                                          mock_config):
        """Test verification uses configurable wait time.
        
        Validates: Requirements 4.2 - Configurable verification wait time
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_thanks_buttons.return_value = []
        
        button = MatchResult(x=100, y=200, width=50, height=25,
                            confidence=0.95, template_name="thanks_button.png")
        
        orchestrator._verify_button_state_changed(button, (0, 0))
        
        # Verify sleep was called with config value
        mock_sleep.assert_called_with(mock_config.click_verify_wait)


class TestProcessTabWithVerification:
    """Tests for process_tab with click verification.
    
    Validates: Requirements 4.2, 4.5
    """

    @patch('time.sleep')
    def test_process_tab_verifies_click_success(self, mock_sleep, orchestrator,
                                                mock_window_capture,
                                                mock_image_recognizer,
                                                mock_auto_clicker,
                                                sample_screenshot):
        """Test process_tab counts only verified clicks.
        
        Validates: Requirements 4.2 - Only count verified clicks
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        thanks_button = MatchResult(x=100, y=200, width=50, height=25,
                                   confidence=0.95, template_name="thanks_button.png")
        thanked_button = MatchResult(x=100, y=200, width=50, height=25,
                                    confidence=0.95, template_name="thanked_button.png")
        
        mock_image_recognizer.find_thanks_buttons.return_value = [thanks_button]
        mock_image_recognizer.find_divider_line.return_value = None
        mock_image_recognizer.filter_buttons_above_divider.return_value = [thanks_button]
        
        # First call returns no thanked, subsequent calls return thanked (after click)
        mock_image_recognizer.find_thanked_buttons.side_effect = [
            [],  # Initial check
            [thanked_button]  # After click verification
        ]
        
        window_rect = (0, 0, 800, 600)
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        assert found == 1
        assert clicked == 1
        assert failed == 0

    @patch('time.sleep')
    def test_process_tab_logs_warning_on_failed_verification(self, mock_sleep, 
                                                              orchestrator,
                                                              mock_window_capture,
                                                              mock_image_recognizer,
                                                              mock_auto_clicker,
                                                              sample_screenshot,
                                                              caplog):
        """Test process_tab logs warning when click verification fails.
        
        Validates: Requirements 4.5 - Log warning when state doesn't change
        """
        import logging
        caplog.set_level(logging.WARNING)
        
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        thanks_button = MatchResult(x=100, y=200, width=50, height=25,
                                   confidence=0.95, template_name="thanks_button.png")
        
        mock_image_recognizer.find_thanks_buttons.return_value = [thanks_button]
        mock_image_recognizer.find_divider_line.return_value = None
        mock_image_recognizer.filter_buttons_above_divider.return_value = [thanks_button]
        
        # Button never changes to thanked
        mock_image_recognizer.find_thanked_buttons.return_value = []
        
        window_rect = (0, 0, 800, 600)
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        assert found == 1
        assert clicked == 0  # Not counted because verification failed
        assert failed == 1  # Counted as failed click
        assert "did not change to thanked state" in caplog.text

    @patch('time.sleep')
    def test_process_tab_skips_failed_click(self, mock_sleep, orchestrator,
                                            mock_window_capture,
                                            mock_image_recognizer,
                                            mock_auto_clicker,
                                            sample_screenshot):
        """Test process_tab skips verification when click fails.
        
        Validates: Requirements 4.5 - Skip button on click failure
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        thanks_button = MatchResult(x=100, y=200, width=50, height=25,
                                   confidence=0.95, template_name="thanks_button.png")
        
        mock_image_recognizer.find_thanks_buttons.return_value = [thanks_button]
        mock_image_recognizer.find_thanked_buttons.return_value = []
        mock_image_recognizer.find_divider_line.return_value = None
        mock_image_recognizer.filter_buttons_above_divider.return_value = [thanks_button]
        
        # Click fails
        mock_auto_clicker.click_button.return_value = False
        
        window_rect = (0, 0, 800, 600)
        found, clicked, failed = orchestrator.process_tab("赞", window_rect)
        
        assert found == 1
        assert clicked == 0
        assert failed == 0  # Click failed, not verification failed


class TestGetPrioritizedTabs:
    """Tests for _get_prioritized_tabs method.
    
    Validates: Requirements 2.2 - Prioritize tabs with "+X" indicator
    """

    def test_prioritized_tabs_default_order_on_screenshot_failure(
        self, orchestrator, mock_window_capture
    ):
        """Test default tab order when screenshot capture fails."""
        mock_window_capture.capture_screenshot.return_value = None
        
        result = orchestrator._get_prioritized_tabs()
        
        assert result == list(orchestrator.DEFAULT_TABS)

    def test_prioritized_tabs_default_order_when_no_indicators(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test default tab order when no indicators are found."""
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.get_tabs_with_indicators.return_value = {
            "赞": False, "关注": False
        }
        
        result = orchestrator._get_prioritized_tabs()
        
        assert result == list(orchestrator.DEFAULT_TABS)

    def test_prioritized_tabs_likes_first_when_has_indicator(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test '赞' tab comes first when it has an indicator.
        
        Validates: Requirements 2.2 - Tab with indicator should be prioritized
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.get_tabs_with_indicators.return_value = {
            "赞": True, "关注": False
        }
        
        result = orchestrator._get_prioritized_tabs()
        
        assert result[0] == "赞"
        assert "关注" in result

    def test_prioritized_tabs_follows_first_when_has_indicator(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test '关注' tab comes first when it has an indicator.
        
        Validates: Requirements 2.2 - Tab with indicator should be prioritized
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.get_tabs_with_indicators.return_value = {
            "赞": False, "关注": True
        }
        
        result = orchestrator._get_prioritized_tabs()
        
        assert result[0] == "关注"
        assert "赞" in result

    def test_prioritized_tabs_both_have_indicators(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test both tabs are prioritized when both have indicators."""
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.get_tabs_with_indicators.return_value = {
            "赞": True, "关注": True
        }
        
        result = orchestrator._get_prioritized_tabs()
        
        # Both should be in result, order follows DEFAULT_TABS since both are prioritized
        assert len(result) == 2
        assert "赞" in result
        assert "关注" in result


class TestRunScanCycleWithPriority:
    """Tests for run_scan_cycle with tab priority.
    
    Validates: Requirements 2.2 - Prioritize tabs with "+X" indicator
    """

    @patch.object(TaskOrchestrator, 'process_tab')
    @patch.object(TaskOrchestrator, '_get_prioritized_tabs')
    def test_scan_cycle_uses_prioritized_tabs(
        self, mock_get_prioritized, mock_process_tab, orchestrator, mock_window_capture
    ):
        """Test scan cycle processes tabs in prioritized order.
        
        Validates: Requirements 2.2 - Process prioritized tabs first
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_get_prioritized.return_value = ["关注", "赞"]  # Reversed order
        mock_process_tab.return_value = (1, 1, 0)  # (found, clicked, failed)
        
        result = orchestrator.run_scan_cycle()
        
        # Verify _get_prioritized_tabs was called
        mock_get_prioritized.assert_called_once()
        
        # Verify tabs were processed in prioritized order
        assert result.tabs_checked == ["关注", "赞"]

    @patch.object(TaskOrchestrator, 'process_tab')
    def test_scan_cycle_prioritizes_tab_with_indicator(
        self, mock_process_tab, orchestrator, mock_window_capture, 
        mock_image_recognizer, sample_screenshot
    ):
        """Test scan cycle prioritizes tab with indicator.
        
        Validates: Requirements 2.2 - Tab with "+X" indicator processed first
        """
        mock_window_capture.find_window.return_value = 12345
        mock_window_capture.is_window_visible.return_value = True
        mock_window_capture.get_window_rect.return_value = (0, 0, 800, 600)
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.get_tabs_with_indicators.return_value = {
            "赞": False, "关注": True
        }
        mock_process_tab.return_value = (1, 1, 0)  # (found, clicked, failed)
        
        result = orchestrator.run_scan_cycle()
        
        # "关注" should be processed first since it has indicator
        assert result.tabs_checked[0] == "关注"


class TestCalculateContentArea:
    """Tests for calculate_content_area method.
    
    Validates: Requirements 5.2 - Scroll within content area only
    """

    def test_calculate_content_area_with_tabs(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test content area calculation when tabs are detected.
        
        Validates: Requirements 5.2 - Content area starts below tabs
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        # Tab at y=50 with height=30
        tab_match = MatchResult(x=100, y=50, width=60, height=30,
                               confidence=0.9, template_name="tab_likes.png")
        mock_image_recognizer.find_tab_buttons.return_value = {"赞": tab_match}
        
        window_rect = (0, 0, 800, 600)
        content_bounds = orchestrator.calculate_content_area(window_rect)
        
        left, top, right, bottom = content_bounds
        
        # Content should start below the tab (y=50 + height/2 + margin)
        # But also at least 1/4 from window top (150)
        assert top >= 150  # At least 1/4 from top
        assert left == 20  # margin
        assert right == 780  # 800 - margin
        assert bottom == 580  # 600 - margin

    def test_calculate_content_area_no_tabs(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test content area calculation when no tabs are detected.
        
        Validates: Requirements 5.2 - Fallback to window-based calculation
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        window_rect = (100, 100, 900, 700)
        content_bounds = orchestrator.calculate_content_area(window_rect)
        
        left, top, right, bottom = content_bounds
        
        # Content top should be at least 1/4 from window top
        expected_min_top = 100 + (700 - 100) // 4  # 250
        assert top >= expected_min_top
        assert left == 120  # 100 + margin
        assert right == 880  # 900 - margin
        assert bottom == 680  # 700 - margin

    def test_calculate_content_area_screenshot_failure(
        self, orchestrator, mock_window_capture, mock_image_recognizer
    ):
        """Test content area calculation when screenshot fails.
        
        Validates: Requirements 5.2 - Graceful fallback on failure
        """
        mock_window_capture.capture_screenshot.return_value = None
        
        window_rect = (0, 0, 800, 600)
        content_bounds = orchestrator.calculate_content_area(window_rect)
        
        left, top, right, bottom = content_bounds
        
        # Should use fallback calculation
        assert top >= 150  # At least 1/4 from top
        assert left == 20
        assert right == 780
        assert bottom == 580

    def test_calculate_content_area_multiple_tabs(
        self, orchestrator, mock_window_capture, mock_image_recognizer, sample_screenshot
    ):
        """Test content area uses lowest tab position.
        
        Validates: Requirements 5.2 - Content below all tabs
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        # Two tabs at different Y positions
        tab_likes = MatchResult(x=100, y=40, width=60, height=30,
                               confidence=0.9, template_name="tab_likes.png")
        tab_follows = MatchResult(x=200, y=60, width=60, height=30,
                                 confidence=0.9, template_name="tab_follows.png")
        mock_image_recognizer.find_tab_buttons.return_value = {
            "赞": tab_likes, "关注": tab_follows
        }
        
        window_rect = (0, 0, 800, 600)
        content_bounds = orchestrator.calculate_content_area(window_rect)
        
        left, top, right, bottom = content_bounds
        
        # Content should start below the lowest tab (y=60)
        # But also at least 1/4 from window top (150)
        assert top >= 150


class TestGetScrollPosition:
    """Tests for get_scroll_position method.
    
    Validates: Requirements 5.2 - Scroll position within content area
    """

    def test_get_scroll_position_center(self, orchestrator):
        """Test scroll position is at center of content area.
        
        Validates: Requirements 5.2 - Scroll at content center
        """
        content_bounds = (100, 200, 700, 500)
        
        scroll_x, scroll_y = orchestrator.get_scroll_position(content_bounds)
        
        expected_x = (100 + 700) // 2  # 400
        expected_y = (200 + 500) // 2  # 350
        assert scroll_x == expected_x
        assert scroll_y == expected_y

    def test_get_scroll_position_within_bounds(self, orchestrator):
        """Test scroll position is always within content bounds.
        
        Validates: Requirements 5.2 - Scroll within bounds
        """
        content_bounds = (50, 100, 750, 550)
        
        scroll_x, scroll_y = orchestrator.get_scroll_position(content_bounds)
        
        left, top, right, bottom = content_bounds
        assert left <= scroll_x <= right
        assert top <= scroll_y <= bottom


class TestRefreshContentWithBounds:
    """Tests for refresh_content with content area bounds.
    
    Validates: Requirements 5.2 - Scroll within content area only
    """

    @patch('time.sleep')
    def test_refresh_content_uses_content_area(
        self, mock_sleep, orchestrator, mock_window_capture, 
        mock_image_recognizer, mock_auto_clicker, sample_screenshot
    ):
        """Test refresh_content scrolls within calculated content area.
        
        Validates: Requirements 5.2 - Scroll within content area
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        
        # Tab at y=50
        tab_match = MatchResult(x=100, y=50, width=60, height=30,
                               confidence=0.9, template_name="tab_likes.png")
        mock_image_recognizer.find_tab_buttons.return_value = {"赞": tab_match}
        
        window_rect = (0, 0, 800, 600)
        orchestrator.refresh_content(window_rect)
        
        # Verify scroll_down was called (no scroll_up per requirement 5.1)
        mock_auto_clicker.scroll_down.assert_called()
        call_args = mock_auto_clicker.scroll_down.call_args
        scroll_x, scroll_y = call_args[0][0], call_args[0][1]
        
        # Scroll position should be within content area bounds
        # Content area: left=20, top>=150, right=780, bottom=580
        assert 20 <= scroll_x <= 780
        assert 150 <= scroll_y <= 580

    @patch('time.sleep')
    def test_refresh_content_scroll_not_at_window_edge(
        self, mock_sleep, orchestrator, mock_window_capture,
        mock_image_recognizer, mock_auto_clicker, sample_screenshot
    ):
        """Test refresh_content does not scroll at window edges.
        
        Validates: Requirements 5.2 - Avoid scrolling at window edges
        """
        mock_window_capture.capture_screenshot.return_value = sample_screenshot
        mock_image_recognizer.find_tab_buttons.return_value = {}
        
        window_rect = (100, 100, 900, 700)
        orchestrator.refresh_content(window_rect)
        
        # Verify scroll position is not at window edges (using scroll_down)
        call_args = mock_auto_clicker.scroll_down.call_args
        scroll_x, scroll_y = call_args[0][0], call_args[0][1]
        
        # Should not be at exact window edges
        assert scroll_x > 100  # Not at left edge
        assert scroll_x < 900  # Not at right edge
        assert scroll_y > 100  # Not at top edge
        assert scroll_y < 700  # Not at bottom edge
