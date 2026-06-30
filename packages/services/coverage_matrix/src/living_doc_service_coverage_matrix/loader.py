# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Input loaders for the coverage-matrix service.

Pure I/O boundary: read JSON files and extract the item arrays. No matching logic.
"""

from pathlib import Path

from living_doc_core.errors import InvalidInputError  # type: ignore[import-untyped]
from living_doc_core.json_utils import read_json  # type: ignore[import-untyped]


def load_doc_input(filepath: str | Path) -> list[dict]:
    """
    Load the User Story + AC doc input.

    Accepts either a bare JSON array of User Story objects or a collector envelope
    object exposing an ``items`` array.

    Args:
        filepath: Path to the doc JSON file (doc-source.json / doc-issues.json)

    Returns:
        List of User Story dictionaries

    Raises:
        FileIOError: If the file is missing or unreadable
        InvalidInputError: If the JSON is malformed or not a US array/envelope
    """
    payload = read_json(filepath)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise InvalidInputError(f"Doc input '{filepath}' must be a JSON array or an object with an 'items' array")


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
