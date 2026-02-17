# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Adapter for Collector-GH package.

This package provides adapter functionality to detect and parse input
from the living-doc-collector-gh action.
"""

__version__ = "1.0.0"

# Export models
from living_doc_adapter_collector_gh.models import (
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterResult,
    CompatibilityWarning,
)

# Export detector functions
from living_doc_adapter_collector_gh.detector import can_handle, extract_version

# Export compatibility checker
from living_doc_adapter_collector_gh.compatibility import check_compatibility

# Export parser
from living_doc_adapter_collector_gh.parser import parse

__all__ = [
    # Version
    "__version__",
    # Models
    "AdapterResult",
    "AdapterItem",
    "AdapterItemTimestamps",
    "AdapterMetadata",
    "CompatibilityWarning",
    # Functions
    "can_handle",
    "extract_version",
    "check_compatibility",
    "parse",
]
