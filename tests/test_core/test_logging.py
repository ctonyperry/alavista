"""
Tests for logging configuration.
"""

import logging

import pytest

from alavista.core.logging import configure_logging, get_logger


class TestConfigureLogging:
    """Test suite for configure_logging function."""
    
    def test_default_configuration(self):
        """Test that logging is configured with default settings."""
        configure_logging()
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0
    
    def test_custom_level(self):
        """Test that custom log level is applied."""
        configure_logging(level="DEBUG")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_json_format(self):
        """Test that JSON format can be enabled."""
        configure_logging(json_format=True)
        
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        
        # Check that formatter contains JSON-like structure
        assert '"timestamp"' in formatter._fmt or 'timestamp' in formatter._fmt
    
    def test_standard_format(self):
        """Test that standard format is used by default."""
        configure_logging(json_format=False)
        
        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        
        # Standard format should contain hyphen separators
        assert '-' in formatter._fmt


class TestGetLogger:
    """Test suite for get_logger function."""
    
    def test_logger_creation(self):
        """Test that loggers are created correctly."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_logger_hierarchy(self):
        """Test that logger hierarchy works correctly."""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")
        
        assert child_logger.parent.name == "parent"
    
    def test_logger_inherits_level(self):
        """Test that child loggers inherit level from root."""
        configure_logging(level="WARNING")
        
        logger = get_logger("test_inherits")
        root_logger = logging.getLogger()
        
        # Effective level should match root
        assert logger.getEffectiveLevel() == root_logger.level


class TestLoggingOutput:
    """Test suite for logging output."""
    
    def test_log_message_output(self, caplog):
        """Test that log messages are properly output."""
        # Capture at root logger level to catch our configured handler
        logger = get_logger("test_output")
        
        with caplog.at_level(logging.INFO, logger="test_output"):
            logger.info("Test message")
        
        # Messages are captured by our stdout handler, check records instead
        assert len(caplog.records) >= 1
        assert any("Test message" in record.message for record in caplog.records)
    
    def test_debug_messages_filtered(self):
        """Test that DEBUG messages are filtered at INFO level."""
        configure_logging(level="INFO")
        logger = get_logger("test_filter")
        
        # At INFO level, logger should not process DEBUG messages
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert not logger.isEnabledFor(logging.DEBUG)
        assert logger.isEnabledFor(logging.INFO)
    
    def test_multiple_loggers(self):
        """Test that multiple loggers work independently."""
        configure_logging(level="INFO")
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both loggers should be properly created and configured
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1.getEffectiveLevel() == logging.INFO
        assert logger2.getEffectiveLevel() == logging.INFO
