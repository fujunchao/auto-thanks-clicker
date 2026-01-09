"""Property-based tests for ConfigManager module.

Feature: auto-thanks-clicker
Property 9: Configuration Round-Trip Consistency
Validates: Requirements 7.4
"""

import os
import tempfile

import pytest
from hypothesis import given, settings, strategies as st

from src.auto_thanks.config_manager import ConfigManager
from src.auto_thanks.models import Config


# Strategy for generating valid Config objects
config_strategy = st.builds(
    Config,
    window_title=st.text(min_size=0, max_size=100),
    check_interval=st.integers(min_value=1, max_value=10000),
    scroll_count=st.integers(min_value=1, max_value=100),
    click_delay=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    confidence_threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    templates_dir=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ""),
    log_file=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ""),
)


@given(config=config_strategy)
@settings(max_examples=100)
def test_property_9_config_round_trip_consistency(config: Config):
    """
    Feature: auto-thanks-clicker
    Property 9: Configuration Round-Trip Consistency
    Validates: Requirements 7.4
    
    For any valid Config object C, saving C to file and then loading from 
    that file SHALL produce a Config object C' where all fields are equal.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        manager = ConfigManager(config_path=temp_path)
        
        # Save the config
        manager.save(config)
        
        # Load it back
        loaded_config = manager.load()
        
        # Verify all fields are equal
        assert loaded_config.window_title == config.window_title
        assert loaded_config.check_interval == config.check_interval
        assert loaded_config.scroll_count == config.scroll_count
        assert abs(loaded_config.click_delay - config.click_delay) < 1e-9
        assert abs(loaded_config.confidence_threshold - config.confidence_threshold) < 1e-9
        assert loaded_config.templates_dir == config.templates_dir
        assert loaded_config.log_file == config.log_file
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_load_nonexistent_file_returns_default():
    """Test that loading from a nonexistent file returns default config."""
    manager = ConfigManager(config_path="nonexistent_config_12345.json")
    config = manager.load()
    default = manager.get_default_config()
    
    assert config.window_title == default.window_title
    assert config.check_interval == default.check_interval
    assert config.scroll_count == default.scroll_count
    assert config.click_delay == default.click_delay
    assert config.confidence_threshold == default.confidence_threshold
    assert config.templates_dir == default.templates_dir
    assert config.log_file == default.log_file


def test_load_invalid_json_returns_default():
    """Test that loading invalid JSON returns default config."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        manager = ConfigManager(config_path=temp_path)
        config = manager.load()
        default = manager.get_default_config()
        
        assert config.window_title == default.window_title
        assert config.check_interval == default.check_interval
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
