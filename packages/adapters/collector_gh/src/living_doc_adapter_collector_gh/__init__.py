# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Adapter for Collector-GH package.

This package provides adapter functionality to detect and parse input
from the living-doc-collector-gh action.

`living-doc-collector-gh` owns the `doc-issues.json` contract and generates
`doc-issues-v1.0.0-schema.json` from its own Pydantic models. This package vendors a pinned
copy under `schemas/` and consumes it; `models.py` is a consumer-side representation kept in
step with that vendored schema via the golden-fixture tests.

See SCHEMA_SYNC.md for the complete synchronization workflow and versioning.
"""

__version__ = "1.0.0"

# Export models
# Export compatibility checker and schema version
from living_doc_adapter_collector_gh.compatibility import SCHEMA_VERSION, check_compatibility

# Export detector functions
from living_doc_adapter_collector_gh.detector import can_handle, extract_version
from living_doc_adapter_collector_gh.models import (
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterResult,
    CompatibilityWarning,
)

# Export parser
from living_doc_adapter_collector_gh.parser import parse

__all__ = [
    # Version
    "__version__",
    "SCHEMA_VERSION",
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
