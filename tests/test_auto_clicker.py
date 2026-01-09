"""Property-based tests for AutoClicker module.

Feature: auto-thanks-clicker
Property 6: Click Coordinate Calculation
Property 7: Scroll Position Bounds
Validates: Requirements 4.1, 4.4, 5.2
"""

import pytest
from hypothesis import given, settings, strategies as st

from src.auto_thanks.auto_clicker import AutoClicker
from src.auto_thanks.models import MatchResult


# Strategy for generating MatchResult objects
match_result_strategy = st.builds(
    MatchResult,
    x=st.integers(min_value=0, max_value=1920),
    y=st.integers(min_value=0, max_value=1080),
    width=st.integers(min_value=10, max_value=200),
    height=st.integers(min_value=10, max_value=100),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    template_name=st.sampled_from(["thanks_button.png", "thanked_button.png"]),
)

# Strategy for window offset
window_offset_strategy = st.tuples(
    st.integers(min_value=0, max_value=500),
    st.integers(min_value=0, max_value=500)
)

# Strategy for window bounds (left, top, right, bottom)
window_bounds_strategy = st.tuples(
    st.integers(min_value=0, max_value=500),   # left
    st.integers(min_value=0, max_value=500),   # top
    st.integers(min_value=501, max_value=1920), # right
    st.integers(min_value=501, max_value=1080)  # bottom
)


@given(match=match_result_strategy, window_offset=window_offset_strategy)
@settings(max_examples=100)
def test_property_6_click_coordinate_calculation(match, window_offset):
    """
    Feature: auto-thanks-clicker
    Property 6: Click Coordinate Calculation
    Validates: Requirements 4.1, 4.4
    
    For any match result with center (x, y) and window offset (ox, oy), 
    the calculated screen click coordinate SHALL be (x + ox, y + oy).
    """
    clicker = AutoClicker(click_delay=0.1)
    
    # Calculate expected coordinates
    expected_x = match.x + window_offset[0]
    expected_y = match.y + window_offset[1]
    
    # Get actual calculated coordinates
    actual_x, actual_y = clicker.calculate_click_coordinates(match, window_offset)
    
    # Property: Calculated coordinates must equal match center + window offset
    assert actual_x == expected_x, f"Expected x={expected_x}, got {actual_x}"
    assert actual_y == expected_y, f"Expected y={expected_y}, got {actual_y}"


@given(
    x=st.integers(min_value=0, max_value=1920),
    y=st.integers(min_value=0, max_value=1080),
    bounds=window_bounds_strategy
)
@settings(max_examples=100)
def test_property_7_scroll_position_bounds(x, y, bounds):
    """
    Feature: auto-thanks-clicker
    Property 7: Scroll Position Bounds
    Validates: Requirements 5.2
    
    For any window with bounds (left, top, right, bottom), all scroll 
    operations SHALL have coordinates (x, y) where left <= x <= right 
    and top <= y <= bottom.
    """
    clicker = AutoClicker(click_delay=0.1)
    
    left, top, right, bottom = bounds
    
    # Property: is_within_bounds correctly validates coordinates
    is_within = clicker.is_within_bounds(x, y, bounds)
    
    expected_within = (left <= x <= right) and (top <= y <= bottom)
    
    assert is_within == expected_within, \
        f"is_within_bounds({x}, {y}, {bounds}) returned {is_within}, expected {expected_within}"


@given(
    x=st.integers(min_value=100, max_value=500),
    y=st.integers(min_value=100, max_value=500)
)
@settings(max_examples=100)
def test_property_7_scroll_within_valid_bounds(x, y):
    """
    Feature: auto-thanks-clicker
    Property 7: Scroll Position Bounds (valid case)
    Validates: Requirements 5.2
    
    For coordinates within a window's bounds, is_within_bounds SHALL return True.
    """
    clicker = AutoClicker(click_delay=0.1)
    
    # Create bounds that contain the point
    bounds = (0, 0, 1920, 1080)
    
    # Property: Point within bounds should return True
    assert clicker.is_within_bounds(x, y, bounds) is True


@given(
    left=st.integers(min_value=100, max_value=200),
    top=st.integers(min_value=100, max_value=200)
)
@settings(max_examples=100)
def test_property_7_scroll_outside_bounds(left, top):
    """
    Feature: auto-thanks-clicker
    Property 7: Scroll Position Bounds (invalid case)
    Validates: Requirements 5.2
    
    For coordinates outside a window's bounds, is_within_bounds SHALL return False.
    """
    clicker = AutoClicker(click_delay=0.1)
    
    # Create bounds
    bounds = (left, top, left + 500, top + 500)
    
    # Test point outside left boundary
    assert clicker.is_within_bounds(left - 10, top + 100, bounds) is False
    
    # Test point outside top boundary
    assert clicker.is_within_bounds(left + 100, top - 10, bounds) is False
    
    # Test point outside right boundary
    assert clicker.is_within_bounds(left + 600, top + 100, bounds) is False
    
    # Test point outside bottom boundary
    assert clicker.is_within_bounds(left + 100, top + 600, bounds) is False


# Unit tests for edge cases and basic functionality

def test_auto_clicker_initialization():
    """Test AutoClicker initializes with correct default values."""
    clicker = AutoClicker()
    assert clicker.click_delay == 0.5
    assert clicker.scroll_amount == 3


def test_auto_clicker_custom_initialization():
    """Test AutoClicker initializes with custom values."""
    clicker = AutoClicker(click_delay=1.0, scroll_amount=5)
    assert clicker.click_delay == 1.0
    assert clicker.scroll_amount == 5


def test_calculate_click_coordinates_zero_offset():
    """Test coordinate calculation with zero offset."""
    clicker = AutoClicker()
    match = MatchResult(x=100, y=200, width=50, height=25, confidence=0.9, template_name="test.png")
    
    coords = clicker.calculate_click_coordinates(match, (0, 0))
    assert coords == (100, 200)


def test_calculate_click_coordinates_with_offset():
    """Test coordinate calculation with non-zero offset."""
    clicker = AutoClicker()
    match = MatchResult(x=100, y=200, width=50, height=25, confidence=0.9, template_name="test.png")
    
    coords = clicker.calculate_click_coordinates(match, (50, 100))
    assert coords == (150, 300)


def test_is_within_bounds_edge_cases():
    """Test is_within_bounds at boundary edges."""
    clicker = AutoClicker()
    bounds = (100, 100, 500, 500)
    
    # Test exact boundaries (should be within)
    assert clicker.is_within_bounds(100, 100, bounds) is True  # top-left corner
    assert clicker.is_within_bounds(500, 500, bounds) is True  # bottom-right corner
    assert clicker.is_within_bounds(100, 500, bounds) is True  # bottom-left corner
    assert clicker.is_within_bounds(500, 100, bounds) is True  # top-right corner
    
    # Test just outside boundaries
    assert clicker.is_within_bounds(99, 100, bounds) is False
    assert clicker.is_within_bounds(100, 99, bounds) is False
    assert clicker.is_within_bounds(501, 100, bounds) is False
    assert clicker.is_within_bounds(100, 501, bounds) is False
