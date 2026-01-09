"""Property-based tests for TaskScheduler module.

Feature: auto-thanks-clicker
Property 8: Interval Configuration Validation
Validates: Requirements 6.2
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, MagicMock

from src.auto_thanks.task_scheduler import TaskScheduler
from src.auto_thanks.task_orchestrator import TaskOrchestrator
from src.auto_thanks.models import Config, ScanResult


def create_mock_orchestrator() -> Mock:
    """Create a mock TaskOrchestrator for testing."""
    mock = Mock(spec=TaskOrchestrator)
    mock.run_scan_cycle = MagicMock(return_value=ScanResult(
        scan_time=None,
        tabs_checked=["赞", "关注"],
        buttons_found=0,
        buttons_clicked=0,
        errors=[]
    ))
    return mock


@given(interval=st.integers(min_value=-1000, max_value=10000))
@settings(max_examples=100)
def test_property_8_interval_configuration_validation(interval: int):
    """
    Feature: auto-thanks-clicker
    Property 8: Interval Configuration Validation
    Validates: Requirements 6.2
    
    For any interval value V provided to the scheduler:
    - If V < 5, the effective interval SHALL be 5 minutes
    - If V > 1440 (24 hours), the effective interval SHALL be 1440 minutes
    - Otherwise, the effective interval SHALL be V minutes
    """
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=interval)
    
    effective_interval = scheduler.get_interval()
    
    if interval < TaskScheduler.MIN_INTERVAL:
        assert effective_interval == TaskScheduler.MIN_INTERVAL, \
            f"Expected {TaskScheduler.MIN_INTERVAL} for input {interval}, got {effective_interval}"
    elif interval > TaskScheduler.MAX_INTERVAL:
        assert effective_interval == TaskScheduler.MAX_INTERVAL, \
            f"Expected {TaskScheduler.MAX_INTERVAL} for input {interval}, got {effective_interval}"
    else:
        assert effective_interval == interval, \
            f"Expected {interval}, got {effective_interval}"


@given(interval=st.integers(min_value=-1000, max_value=10000))
@settings(max_examples=100)
def test_property_8_set_interval_validation(interval: int):
    """
    Feature: auto-thanks-clicker
    Property 8: Interval Configuration Validation (via set_interval)
    Validates: Requirements 6.2
    
    Tests that set_interval also validates the interval bounds.
    """
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    # Set a new interval
    scheduler.set_interval(interval)
    effective_interval = scheduler.get_interval()
    
    if interval < TaskScheduler.MIN_INTERVAL:
        assert effective_interval == TaskScheduler.MIN_INTERVAL
    elif interval > TaskScheduler.MAX_INTERVAL:
        assert effective_interval == TaskScheduler.MAX_INTERVAL
    else:
        assert effective_interval == interval


def test_scheduler_start_stop():
    """Test that scheduler can be started and stopped."""
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    assert not scheduler.is_running()
    
    scheduler.start()
    assert scheduler.is_running()
    
    scheduler.stop()
    assert not scheduler.is_running()


def test_scheduler_run_now():
    """Test that run_now executes the scan immediately."""
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    result = scheduler.run_now()
    
    assert result is not None
    mock_orchestrator.run_scan_cycle.assert_called_once()


def test_scheduler_double_start():
    """Test that starting an already running scheduler is handled gracefully."""
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    scheduler.start()
    scheduler.start()  # Should not raise
    
    assert scheduler.is_running()
    scheduler.stop()


def test_scheduler_double_stop():
    """Test that stopping an already stopped scheduler is handled gracefully."""
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    scheduler.stop()  # Should not raise
    assert not scheduler.is_running()


def test_scheduler_get_last_result():
    """Test that get_last_result returns the last scan result."""
    mock_orchestrator = create_mock_orchestrator()
    scheduler = TaskScheduler(mock_orchestrator, interval_minutes=60)
    
    # Initially no result
    assert scheduler.get_last_result() is None
    
    # After running, should have a result
    scheduler.run_now()
    result = scheduler.get_last_result()
    
    assert result is not None
    assert result.tabs_checked == ["赞", "关注"]
