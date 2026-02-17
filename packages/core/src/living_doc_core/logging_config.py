# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Logging configuration utilities.
"""

import logging


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure and return a logger for the Living Documentation toolkit.

    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO

    Returns:
        Configured logger instance named "living_doc"
    """
    logger = logging.getLogger("living_doc")

    # Set log level based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Set format: [LEVEL] message
    formatter = logging.Formatter("[{levelname}] {message}", style="{")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
