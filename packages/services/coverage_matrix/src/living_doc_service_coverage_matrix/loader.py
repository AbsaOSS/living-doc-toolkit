# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Input loaders for the coverage-matrix service.

Pure I/O boundary: read JSON files and extract the item arrays. No matching logic.
"""

from pathlib import Path

from living_doc_core.errors import InvalidInputError  # type: ignore[import-untyped]
from living_doc_core.json_utils import read_json  # type: ignore[import-untyped]

from living_doc_service_coverage_matrix.schema_validation import is_doc_source_envelope, validate_doc_source


def load_doc_input(filepath: str | Path) -> dict:
    """
    Load the doc-source input and split it into its object groups.

    Accepts the doc-source envelope (an object exposing ``user_stories``,
    ``functionalities`` and ``features`` arrays), a legacy collector envelope with an
    ``items`` array, or a bare JSON array of User Story objects. Full doc-source
    envelopes (carrying ``metadata`` and ``warnings``) are validated against the
    bundled ``doc-source-v1.0.0`` JSON Schema.

    Args:
        filepath: Path to the doc JSON file (doc-source.json / doc-issues.json)

    Returns:
        Dict with ``user_stories``, ``functionalities`` and ``features`` lists

    Raises:
        FileIOError: If the file is missing or unreadable
        InvalidInputError: If the JSON is malformed, fails schema validation, or is
            not a US array/envelope
    """
    payload = read_json(filepath)
    if isinstance(payload, list):
        return {"user_stories": payload, "functionalities": [], "features": []}
    if isinstance(payload, dict):
        if is_doc_source_envelope(payload):
            validate_doc_source(payload)
        if isinstance(payload.get("user_stories"), list):
            return {
                "user_stories": payload["user_stories"],
                "functionalities": payload.get("functionalities") or [],
                "features": payload.get("features") or [],
            }
        if isinstance(payload.get("items"), list):
            return {"user_stories": payload["items"], "functionalities": [], "features": []}
    raise InvalidInputError(
        f"Doc input '{filepath}' must be a JSON array or an object with a " "'user_stories' (or legacy 'items') array"
    )


def load_tests_input(filepath: str | Path) -> list[dict]:
    """
    Load the ui-tests input.

    Args:
        filepath: Path to the ui-tests JSON file

    Returns:
        List of test scenario dictionaries

    Raises:
        FileIOError: If the file is missing or unreadable
        InvalidInputError: If the JSON is malformed or has no ``items`` array
    """
    payload = read_json(filepath)
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise InvalidInputError(f"Tests input '{filepath}' must contain an 'items' array")
