# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Schema export for Pydantic models.

Exports Pydantic models to JSON Schema format as an independent artifact.

Schemas are saved to the `schemas/` directory next to the src/ directory,
making them available for distribution and use by downstream consumers.

See SCHEMA_SYNC.md for details.
"""

import json
from pathlib import Path

from living_doc_adapter_collector_gh.models import AdapterResult


def get_default_schema_path() -> Path:
    """
    Get the default schema export directory path.

    Returns:
        Path to schemas/ directory (packages/adapters/collector_gh/schemas/)
    """
    # Navigate from src/living_doc_adapter_collector_gh/ to packages/adapters/collector_gh/schemas/
    package_root = Path(__file__).parent.parent.parent  # Go up to collector_gh/
    schemas_dir = package_root / "schemas"
    return schemas_dir


def export_schema(output_path: str | Path | None = None) -> dict:
    """
    Export the AdapterResult model schema to JSON Schema format.

    This schema represents the authoritative input contract for the data format.

    Args:
        output_path: Optional file path to write schema to. If None, uses default
                     location with version: packages/adapters/collector_gh/schemas/doc-issues-v1.0.0-schema.json

    Returns:
        Dictionary containing the JSON Schema.

    Example:
        >>> schema = export_schema()
        >>> print(schema['$defs']['AdapterMetadataSource'])

        >>> export_schema('custom-location.json')
    """
    schema = AdapterResult.model_json_schema()
    # Pin schema version independently of adapter version
    schema["$schema_version"] = "1.0.0"

    # Use default location if not provided
    if output_path is None:
        schemas_dir = get_default_schema_path()
        schema_version = get_schema_version()
        output_path = schemas_dir / f"doc-issues-v{schema_version}-schema.json"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema exported to: {output_file}")

    return schema


def get_schema_version() -> str:
    """
    Get the version of the input contract schema.

    This is independent of the adapter package version and represents
    the version of the doc-issues.json input schema.

    Returns:
        Version string (semver format)
    """
    return "1.0.0"


if __name__ == "__main__":
    import sys

    # CLI usage:
    #   python -m living_doc_adapter_collector_gh.schema_export  # Uses default location with version
    #   python -m living_doc_adapter_collector_gh.schema_export output.json  # Custom location
    output = sys.argv[1] if len(sys.argv) > 1 else None
    export_schema(output)
    if output is None:
        schema_version = get_schema_version()
        print(f"Default location: {get_default_schema_path() / f'doc-issues-v{schema_version}-schema.json'}")
