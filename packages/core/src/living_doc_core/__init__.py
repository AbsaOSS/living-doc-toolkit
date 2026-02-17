# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Core Utilities package.

This package provides reusable, service-agnostic helper utilities.
"""

__version__ = "1.0.0"

# Export error types
from living_doc_core.errors import (
    AdapterError,
    FileIOError,
    InvalidInputError,
    NormalizationError,
    SchemaValidationError,
    ToolkitError,
)

# Export JSON utilities
from living_doc_core.json_utils import read_json, validate_json_structure, write_json

# Export logging utilities
from living_doc_core.logging_config import setup_logging

# Export markdown utilities
from living_doc_core.markdown_utils import extract_lists, normalize_heading, split_by_headings

__all__ = [
    # Version
    "__version__",
    # Errors
    "ToolkitError",
    "InvalidInputError",
    "AdapterError",
    "SchemaValidationError",
    "NormalizationError",
    "FileIOError",
    # JSON utilities
    "read_json",
    "write_json",
    "validate_json_structure",
    # Logging
    "setup_logging",
    # Markdown
    "split_by_headings",
    "normalize_heading",
    "extract_lists",
]
