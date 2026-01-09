"""Property-based tests for ImageRecognizer module.

Feature: auto-thanks-clicker
Property 3: Template Matching Completeness
Property 4: Button Filtering by Divider Position
Property 5: Thanks vs Thanked Button Classification
Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

import os
import tempfile

import cv2
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st, assume

from src.auto_thanks.image_recognizer import ImageRecognizer
from src.auto_thanks.models import MatchResult


# Strategy for generating MatchResult objects
match_result_strategy = st.builds(
    MatchResult,
    x=st.integers(min_value=0, max_value=1920),
    y=st.integers(min_value=0, max_value=1080),
    width=st.integers(min_value=10, max_value=200),
    height=st.integers(min_value=10, max_value=100),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    template_name=st.sampled_from(["thanks_button.png", "thanked_button.png", "divider_line.png"]),
)

# Strategy for generating lists of MatchResult (buttons)
buttons_list_strategy = st.lists(match_result_strategy, min_size=0, max_size=20)

# Strategy for divider Y coordinate (can be None or an integer)
divider_y_strategy = st.one_of(
    st.none(),
    st.integers(min_value=0, max_value=1080)
)


@given(buttons=buttons_list_strategy, divider_y=st.integers(min_value=0, max_value=1080))
@settings(max_examples=30)
def test_property_4_button_filtering_by_divider_position(buttons, divider_y):
    """
    Feature: auto-thanks-clicker
    Property 4: Button Filtering by Divider Position
    Validates: Requirements 3.3, 3.5
    
    For any list of button match results and a divider Y coordinate, 
    the filter_buttons_above_divider function SHALL return only buttons 
    where button.y < divider_y. For any button in the filtered list, 
    its Y coordinate SHALL be strictly less than the divider Y coordinate.
    """
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=0.8)
    
    filtered = recognizer.filter_buttons_above_divider(buttons, divider_y)
    
    # Property: All filtered buttons must have y < divider_y
    for btn in filtered:
        assert btn.y < divider_y, f"Button at y={btn.y} should not be in filtered list (divider_y={divider_y})"
    
    # Property: All buttons with y < divider_y must be in filtered list
    expected_count = sum(1 for btn in buttons if btn.y < divider_y)
    assert len(filtered) == expected_count, f"Expected {expected_count} buttons, got {len(filtered)}"


@given(buttons=buttons_list_strategy)
@settings(max_examples=30)
def test_property_4_no_divider_returns_all_buttons(buttons):
    """
    Feature: auto-thanks-clicker
    Property 4: Button Filtering by Divider Position (edge case)
    Validates: Requirements 3.5
    
    If no divider line is found (divider_y is None), the function SHALL 
    return all visible buttons.
    """
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=0.8)
    
    filtered = recognizer.filter_buttons_above_divider(buttons, None)
    
    # When divider_y is None, all buttons should be returned
    assert len(filtered) == len(buttons)
    for original, returned in zip(buttons, filtered):
        assert original.x == returned.x
        assert original.y == returned.y


@given(
    thanks_positions=st.lists(
        st.tuples(st.integers(50, 400), st.integers(50, 400)),
        min_size=1,
        max_size=5,
        unique=True
    ),
    thanked_positions=st.lists(
        st.tuples(st.integers(50, 400), st.integers(50, 400)),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=30)
def test_property_5_thanks_vs_thanked_classification(thanks_positions, thanked_positions):
    """
    Feature: auto-thanks-clicker
    Property 5: Thanks vs Thanked Button Classification
    Validates: Requirements 3.4, 4.3
    
    For any screenshot, the intersection of find_thanks_buttons results 
    and find_thanked_buttons results SHALL be empty (no button is 
    classified as both).
    """
    # Template dimensions
    template_w, template_h = 50, 25
    
    def positions_overlap(p1, p2):
        return abs(p1[0] - p2[0]) < template_w and abs(p1[1] - p2[1]) < template_h
    
    # Check no overlap between thanks and thanked positions
    for tp in thanks_positions:
        for thp in thanked_positions:
            if positions_overlap(tp, thp):
                assume(False)
    
    # Check no overlap within thanks positions
    for i, p1 in enumerate(thanks_positions):
        for p2 in thanks_positions[i+1:]:
            if positions_overlap(p1, p2):
                assume(False)
    
    # Check no overlap within thanked positions
    for i, p1 in enumerate(thanked_positions):
        for p2 in thanked_positions[i+1:]:
            if positions_overlap(p1, p2):
                assume(False)

    # Create a test image with white background
    img_height, img_width = 500, 500
    screenshot = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255

    # Create temporary templates directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create "thanks" template - blue with red border pattern
        thanks_template = np.ones((template_h, template_w, 3), dtype=np.uint8) * 255
        thanks_template[2:-2, 2:-2] = (255, 0, 0)  # Blue fill
        thanks_template[0:2, :] = (0, 0, 255)  # Red top border
        thanks_template[-2:, :] = (0, 0, 255)  # Red bottom border
        thanks_path = os.path.join(temp_dir, "thanks_button.png")
        cv2.imwrite(thanks_path, thanks_template)

        # Create "thanked" template - green with yellow border pattern
        thanked_template = np.ones((template_h, template_w, 3), dtype=np.uint8) * 255
        thanked_template[2:-2, 2:-2] = (0, 255, 0)  # Green fill
        thanked_template[0:2, :] = (0, 255, 255)  # Yellow top border
        thanked_template[-2:, :] = (0, 255, 255)  # Yellow bottom border
        thanked_path = os.path.join(temp_dir, "thanked_button.png")
        cv2.imwrite(thanked_path, thanked_template)

        # Draw thanks buttons on screenshot
        for x, y in thanks_positions:
            if y + template_h <= img_height and x + template_w <= img_width:
                screenshot[y:y+template_h, x:x+template_w] = thanks_template

        # Draw thanked buttons on screenshot
        for x, y in thanked_positions:
            if y + template_h <= img_height and x + template_w <= img_width:
                screenshot[y:y+template_h, x:x+template_w] = thanked_template

        recognizer = ImageRecognizer(templates_dir=temp_dir, confidence_threshold=0.95)
        recognizer.load_templates()

        thanks_results = recognizer.find_thanks_buttons(screenshot)
        thanked_results = recognizer.find_thanked_buttons(screenshot)

        # Extract center positions for comparison
        thanks_centers = {(r.x, r.y) for r in thanks_results}
        thanked_centers = {(r.x, r.y) for r in thanked_results}

        # Property: No button should be classified as both thanks and thanked
        intersection = thanks_centers & thanked_centers
        assert len(intersection) == 0, f"Buttons classified as both: {intersection}"



@given(
    num_templates=st.integers(min_value=1, max_value=3),
    positions=st.lists(
        st.tuples(st.integers(10, 400), st.integers(10, 400)),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=30)
def test_property_3_template_matching_completeness(num_templates, positions):
    """
    Feature: auto-thanks-clicker
    Property 3: Template Matching Completeness
    Validates: Requirements 3.1, 3.2
    
    For any screenshot image containing N instances of a template image 
    at positions P1...Pn, the find_template function SHALL return exactly 
    N match results, each with coordinates within a tolerance of the 
    actual positions.
    """
    # Create a test image
    img_height, img_width = 500, 500
    screenshot = np.zeros((img_height, img_width, 3), dtype=np.uint8)
    screenshot[:] = (128, 128, 128)  # Gray background
    
    # Create a distinctive template
    template_h, template_w = 25, 50
    template = np.zeros((template_h, template_w, 3), dtype=np.uint8)
    template[:] = (0, 0, 255)  # Red rectangle
    # Add a distinctive pattern
    template[5:20, 10:40] = (255, 255, 0)  # Cyan inner rectangle
    
    with tempfile.TemporaryDirectory() as temp_dir:
        template_path = os.path.join(temp_dir, "test_template.png")
        cv2.imwrite(template_path, template)
        
        # Filter positions to ensure templates fit and don't overlap
        valid_positions = []
        for x, y in positions:
            if y + template_h <= img_height and x + template_w <= img_width:
                # Check for overlap with existing positions
                overlaps = False
                for vx, vy in valid_positions:
                    if abs(x - vx) < template_w and abs(y - vy) < template_h:
                        overlaps = True
                        break
                if not overlaps:
                    valid_positions.append((x, y))
        
        assume(len(valid_positions) > 0)  # Need at least one valid position
        
        # Place templates at valid positions
        for x, y in valid_positions:
            screenshot[y:y+template_h, x:x+template_w] = template
        
        recognizer = ImageRecognizer(templates_dir=temp_dir, confidence_threshold=0.95)
        recognizer.load_templates()
        
        results = recognizer.find_template(screenshot, "test_template.png")
        
        # Property: Should find exactly the number of placed templates
        assert len(results) == len(valid_positions), \
            f"Expected {len(valid_positions)} matches, got {len(results)}"
        
        # Property: Each result should be within tolerance of actual position
        tolerance = 5  # pixels
        result_centers = [(r.x, r.y) for r in results]
        
        for x, y in valid_positions:
            expected_center = (x + template_w // 2, y + template_h // 2)
            found = False
            for rx, ry in result_centers:
                if abs(rx - expected_center[0]) <= tolerance and abs(ry - expected_center[1]) <= tolerance:
                    found = True
                    break
            assert found, f"Template at {(x, y)} not found in results (expected center {expected_center})"


# Unit tests for edge cases

def test_find_template_with_empty_screenshot():
    """Test that find_template handles empty screenshot gracefully."""
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=0.8)
    
    # Empty array
    empty = np.array([])
    results = recognizer.find_template(empty, "test.png")
    assert results == []
    
    # None
    results = recognizer.find_template(None, "test.png")
    assert results == []


def test_find_template_with_nonexistent_template():
    """Test that find_template handles missing template gracefully."""
    recognizer = ImageRecognizer(templates_dir="nonexistent_dir", confidence_threshold=0.8)
    
    screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
    results = recognizer.find_template(screenshot, "nonexistent.png")
    assert results == []


def test_load_templates_with_nonexistent_directory():
    """Test that load_templates handles missing directory gracefully."""
    recognizer = ImageRecognizer(templates_dir="nonexistent_dir_12345", confidence_threshold=0.8)
    templates = recognizer.load_templates()
    assert templates == {}


def test_find_divider_line_returns_none_when_not_found():
    """Test that find_divider_line returns None when divider not found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        recognizer = ImageRecognizer(templates_dir=temp_dir, confidence_threshold=0.8)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = recognizer.find_divider_line(screenshot)
        assert result is None


def test_find_tab_buttons_returns_empty_when_not_found():
    """Test that find_tab_buttons returns empty dict when tabs not found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        recognizer = ImageRecognizer(templates_dir=temp_dir, confidence_threshold=0.8)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = recognizer.find_tab_buttons(screenshot)
        assert result == {}


def test_confidence_threshold_clamping():
    """Test that confidence threshold is clamped to valid range."""
    # Test lower bound
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=-0.5)
    assert recognizer.confidence_threshold == 0.0
    
    # Test upper bound
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=1.5)
    assert recognizer.confidence_threshold == 1.0
    
    # Test valid value
    recognizer = ImageRecognizer(templates_dir="templates", confidence_threshold=0.75)
    assert recognizer.confidence_threshold == 0.75
