# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Version compatibility checking for the collector-gh adapter.

This module provides functions to check if a producer version is within
the confirmed compatible range.
"""

from packaging.version import Version, InvalidVersion

from living_doc_adapter_collector_gh.models import CompatibilityWarning

# Confirmed compatible version range
CONFIRMED_MIN = "1.0.0"
CONFIRMED_MAX = "2.0.0"  # Exclusive upper bound


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
                    f"Producer version {version} is outside confirmed range"
                    f" >={CONFIRMED_MIN},<{CONFIRMED_MAX}"
                ),
                context="metadata.generator.version",
            )
        ]
    except InvalidVersion:
        return [
            CompatibilityWarning(
                code="INVALID_VERSION",
                message=f"Producer version '{version}' is not a valid semantic version",
                context="metadata.generator.version",
            )
        ]
