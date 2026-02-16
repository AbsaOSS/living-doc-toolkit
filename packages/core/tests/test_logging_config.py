# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for logging configuration.
"""

import logging

from living_doc_core.logging_config import setup_logging


def test_setup_logging_default_level():
    """Test that setup_logging returns INFO level by default."""
    logger = setup_logging(verbose=False)
    assert logger.name == "living_doc"
    assert logger.level == logging.INFO


def test_setup_logging_verbose_level():
    """Test that setup_logging returns DEBUG level when verbose=True."""
    logger = setup_logging(verbose=True)
    assert logger.name == "living_doc"
    assert logger.level == logging.DEBUG


def test_logging_format_matches_spec():
    """Test that log format matches [LEVEL] message."""
    logger = setup_logging(verbose=False)

    # Get the formatter from the first handler
    assert len(logger.handlers) > 0
    handler = logger.handlers[0]
    formatter = handler.formatter

    # Test format by creating a log record
    record = logging.LogRecord(
        name="living_doc",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    assert formatted == "[INFO] Test message"


def test_logging_format_with_different_levels():
    """Test log format with different log levels."""
    logger = setup_logging(verbose=True)
    handler = logger.handlers[0]
    formatter = handler.formatter

    # Test DEBUG level
    record = logging.LogRecord(
        name="living_doc",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Debug message",
        args=(),
        exc_info=None,
    )
    assert formatter.format(record) == "[DEBUG] Debug message"

    # Test WARNING level
    record = logging.LogRecord(
        name="living_doc",
        level=logging.WARNING,
        pathname="test.py",
        lineno=1,
        msg="Warning message",
        args=(),
        exc_info=None,
    )
    assert formatter.format(record) == "[WARNING] Warning message"

    # Test ERROR level
    record = logging.LogRecord(
        name="living_doc",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Error message",
        args=(),
        exc_info=None,
    )
    assert formatter.format(record) == "[ERROR] Error message"


def test_logger_has_stream_handler():
    """Test that logger has a StreamHandler configured."""
    logger = setup_logging()
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_logger_does_not_propagate():
    """Test that logger does not propagate to root logger."""
    logger = setup_logging()
    assert logger.propagate is False


def test_multiple_setup_calls_clear_handlers():
    """Test that calling setup_logging multiple times doesn't duplicate handlers."""
    logger1 = setup_logging(verbose=False)
    handler_count_1 = len(logger1.handlers)

    logger2 = setup_logging(verbose=True)
    handler_count_2 = len(logger2.handlers)

    # Both should have exactly 1 handler
    assert handler_count_1 == 1
    assert handler_count_2 == 1
    assert logger1 is logger2  # Same logger instance
