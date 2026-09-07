# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Version compatibility checking for the collector-gh adapter.

This module provides functions to check if a producer version is within
the confirmed compatible range.

`living-doc-collector-gh` owns the `doc-issues.json` contract and generates its schema;
this repo vendors a pinned copy and, when it receives a `doc-issues.json`, checks that the
producer version (`metadata.producer.version`) is within the confirmed compatible range.

See SCHEMA_SYNC.md for the full synchronization workflow.
"""

from packaging.version import InvalidVersion, Version

from living_doc_adapter_collector_gh.models import CompatibilityWarning

# Confirmed compatible version range
# Maps to producer repo releases:
# https://github.com/AbsaOSS/living-doc-collector-gh/releases
# TODO(before v1 release): widen to the confirmed 1.0.0 line once collector-gh tags
# v1.0.0 — see SCHEMA_SYNC.md. The floor tracks collector-gh's current package version
# (0.1.1); a higher floor flags every real 0.1.x payload with a spurious VERSION_MISMATCH.
CONFIRMED_MIN = "0.1.1"
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
