# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Living Documentation Adapter for Collector-GH package.

This package provides adapter functionality to detect and parse input
from the living-doc-collector-gh action.

SCHEMA SYNCHRONIZATION: Pydantic-First Pattern
==============================================

This repo defines and exports the input contract:

1. Pydantic models (models.py) are the single source of truth
2. Export Pydantic models to JSON Schema as an artifact (schema_export.py)
3. Schema is saved with version: packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json
4. Publish schema for downstream consumers to obtain independently

To export the schema (saved to default location with version):

    python -m living_doc_adapter_collector_gh.schema_export

Or to a custom location:

    python -m living_doc_adapter_collector_gh.schema_export custom-output.json

See SCHEMA_SYNC.md for the complete synchronization workflow and versioning.
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

# Export compatibility checker and schema version
from living_doc_adapter_collector_gh.compatibility import check_compatibility, SCHEMA_VERSION

# Export parser
from living_doc_adapter_collector_gh.parser import parse

# Export schema export function
from living_doc_adapter_collector_gh.schema_export import export_schema

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
    "export_schema",
]
