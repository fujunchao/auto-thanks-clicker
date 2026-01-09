"""Tests for the logger module."""

import logging
import os
import tempfile
import pytest

from src.auto_thanks.logger import (
    setup_logging,
    get_logger,
    set_log_level,
    shutdown_logging,
    add_file_handler,
    DEFAULT_LOG_FILE,
    DEFAULT_MAX_BYTES,
    DEFAULT_BACKUP_COUNT,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_logger(self, tmp_path):
        """Test that setup_logging creates a properly configured logger."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        assert logger is not None
        assert logger.name == "auto_thanks"
        assert logger.level == logging.INFO
        
        # Clean up
        shutdown_logging()

    def test_setup_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates the log file."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        # Write a log message
        logger.info("Test message")
        
        # Verify file was created
        assert log_file.exists()
        
        # Clean up
        shutdown_logging()

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates the log directory if needed."""
        log_dir = tmp_path / "logs" / "subdir"
        log_file = log_dir / "test.log"
        
        logger = setup_logging(log_file=str(log_file), console_output=False)
        logger.info("Test message")
        
        assert log_dir.exists()
        assert log_file.exists()
        
        # Clean up
        shutdown_logging()

    def test_setup_logging_with_custom_format(self, tmp_path):
        """Test that custom log format is applied."""
        log_file = tmp_path / "test.log"
        custom_format = "%(levelname)s - %(message)s"
        
        logger = setup_logging(
            log_file=str(log_file),
            log_format=custom_format,
            console_output=False
        )
        logger.info("Test message")
        
        # Read the log file and verify format
        with open(log_file, 'r') as f:
            content = f.read()
        
        assert "INFO - Test message" in content
        
        # Clean up
        shutdown_logging()

    def test_setup_logging_clears_existing_handlers(self, tmp_path):
        """Test that setup_logging clears existing handlers."""
        log_file = tmp_path / "test.log"
        
        # Setup logging twice
        setup_logging(log_file=str(log_file), console_output=False)
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        # Should only have one file handler
        file_handlers = [h for h in logger.handlers 
                        if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        
        # Clean up
        shutdown_logging()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self, tmp_path):
        """Test that get_logger returns a logger instance."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), console_output=False)
        
        logger = get_logger("test_module")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        
        # Clean up
        shutdown_logging()

    def test_get_logger_with_name(self, tmp_path):
        """Test that get_logger uses the provided name."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), console_output=False)
        
        logger = get_logger("my_custom_module")
        
        assert logger.name == "my_custom_module"
        
        # Clean up
        shutdown_logging()


class TestSetLogLevel:
    """Tests for set_log_level function."""

    def test_set_log_level_changes_level(self, tmp_path):
        """Test that set_log_level changes the logging level."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        # Initially INFO
        assert logger.level == logging.INFO
        
        # Change to DEBUG
        set_log_level(logging.DEBUG)
        
        assert logger.level == logging.DEBUG
        
        # Clean up
        shutdown_logging()

    def test_set_log_level_affects_handlers(self, tmp_path):
        """Test that set_log_level changes handler levels too."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        set_log_level(logging.WARNING)
        
        for handler in logger.handlers:
            assert handler.level == logging.WARNING
        
        # Clean up
        shutdown_logging()


class TestAddFileHandler:
    """Tests for add_file_handler function."""

    def test_add_file_handler_creates_handler(self, tmp_path):
        """Test that add_file_handler adds a new file handler."""
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"
        
        logger = setup_logging(log_file=str(log_file1), console_output=False)
        initial_handler_count = len(logger.handlers)
        
        add_file_handler(str(log_file2))
        
        assert len(logger.handlers) == initial_handler_count + 1
        
        # Clean up
        shutdown_logging()

    def test_add_file_handler_writes_to_file(self, tmp_path):
        """Test that the added handler writes to its file."""
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"
        
        logger = setup_logging(log_file=str(log_file1), console_output=False)
        add_file_handler(str(log_file2))
        
        logger.info("Test message")
        
        # Both files should have the message
        assert log_file1.exists()
        assert log_file2.exists()
        
        with open(log_file2, 'r') as f:
            content = f.read()
        assert "Test message" in content
        
        # Clean up
        shutdown_logging()


class TestShutdownLogging:
    """Tests for shutdown_logging function."""

    def test_shutdown_logging_removes_handlers(self, tmp_path):
        """Test that shutdown_logging removes all handlers."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), console_output=False)
        
        assert len(logger.handlers) > 0
        
        shutdown_logging()
        
        assert len(logger.handlers) == 0

    def test_shutdown_logging_can_be_called_multiple_times(self, tmp_path):
        """Test that shutdown_logging can be called safely multiple times."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), console_output=False)
        
        # Should not raise any errors
        shutdown_logging()
        shutdown_logging()


class TestLogRotation:
    """Tests for log file rotation."""

    def test_log_rotation_creates_backup_files(self, tmp_path):
        """Test that log rotation creates backup files when size limit is reached."""
        log_file = tmp_path / "test.log"
        
        # Use very small max_bytes to trigger rotation quickly
        logger = setup_logging(
            log_file=str(log_file),
            max_bytes=100,  # Very small to trigger rotation
            backup_count=2,
            console_output=False
        )
        
        # Write enough data to trigger rotation
        for i in range(50):
            logger.info(f"This is a test message number {i} with some extra text to fill space")
        
        # Check that backup files were created
        log_files = list(tmp_path.glob("test.log*"))
        assert len(log_files) > 1  # Original + at least one backup
        
        # Clean up
        shutdown_logging()
