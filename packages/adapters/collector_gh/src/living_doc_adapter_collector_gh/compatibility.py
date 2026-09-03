# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Version compatibility checking for the collector-gh adapter.

This module provides functions to check if a producer version is within
the confirmed compatible range.

SCHEMA SYNCHRONIZATION PATTERN
===============================

This repo (living-doc-toolkit) is the schema producer:

1. Defines Pydantic models as single source of truth (models.py)
2. Exports them to JSON Schema (schema_export.py)
3. Publishes schema as independent artifact

Collector-gh repo (independent):

1. Downloads published schema
2. Uses it to validate doc-issues.json
3. Publishes validated data
4. No direct code dependency

When this repo receives doc-issues.json from collector-gh, we check
that the producer version is within our confirmed compatible range.

See SCHEMA_SYNC.md for full synchronization workflow.
"""

from packaging.version import InvalidVersion, Version

from living_doc_adapter_collector_gh.models import CompatibilityWarning

# Confirmed compatible version range
# Maps to producer repo releases:
# https://github.com/AbsaOSS/living-doc-collector-gh/releases
CONFIRMED_MIN = "1.0.0"
CONFIRMED_MAX = "2.0.0"  # Exclusive upper bound

# Schema version (independent of adapter package version)
# See schema_export.py for details
SCHEMA_VERSION = "1.0.0"


def check_compatibility(version: str) -> list[CompatibilityWarning]:
    """
    Check if the producer version is within the confirmed compatible range.

    Args:
        version: Version string to check (semver format)

    Returns:
        List of compatibility warnings. Empty list if version is compatible.
    """
    try:
        parsed_version = Version(version)
        min_version = Version(CONFIRMED_MIN)
        max_version = Version(CONFIRMED_MAX)

        if min_version <= parsed_version < max_version:
            return []

        # Version is outside confirmed range
        return [
            CompatibilityWarning(
                code="VERSION_MISMATCH",
                message=(
                    f"Producer version {version} is outside confirmed range" f" >={CONFIRMED_MIN},<{CONFIRMED_MAX}"
                ),
                context="metadata.producer.version",
            )
        ]
    except InvalidVersion:
        return [
            CompatibilityWarning(
                code="INVALID_VERSION",
                message=f"Producer version '{version}' is not a valid semantic version",
                context="metadata.producer.version",
            )
        ]
