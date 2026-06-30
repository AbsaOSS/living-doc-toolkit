# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Producer detection logic for the collector-gh adapter.

This module provides functions to detect if an input payload is from
the living-doc-collector-gh action and to extract version information.
"""

from living_doc_core.errors import AdapterError  # type: ignore[import-untyped]


def can_handle(payload: dict) -> bool:
    """
    Check if the adapter can handle the given payload.

    Args:
        payload: Input payload dictionary to check

    Returns:
        True if the payload is from living-doc-collector-gh, False otherwise
    """
    try:
        producer_name = payload.get("metadata", {}).get("producer", {}).get("name")
        return producer_name == "AbsaOSS/living-doc-collector-gh"
    except Exception:  # pylint: disable=broad-exception-caught
        # Handle AttributeError, TypeError gracefully
        return False


def extract_version(payload: dict) -> str:
    """
    Extract the producer version from the payload.

    Args:
        payload: Input payload dictionary

    Returns:
        Version string from the payload

    Raises:
        AdapterError: If the version cannot be extracted
    """
    try:
        version = payload["metadata"]["producer"]["version"]
        if not version:
            raise AdapterError("Producer version is empty in metadata.producer.version")
        return version
    except (KeyError, TypeError) as e:
        raise AdapterError(f"Missing or invalid metadata.producer.version in payload: {e}") from e
