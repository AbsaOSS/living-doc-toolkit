# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
JSON utilities for reading, writing, and validating JSON files.
"""

import json
from pathlib import Path

from living_doc_core.errors import FileIOError, InvalidInputError


def read_json(filepath: str | Path) -> dict:
    """
    Read and parse a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        Parsed JSON as a dictionary

    Raises:
        FileIOError: If file not found or cannot be read
        InvalidInputError: If JSON is malformed
    """
    path = Path(filepath)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileIOError(f"File '{filepath}' not found") from e
    except PermissionError as e:
        raise FileIOError(f"Permission denied reading '{filepath}'") from e
    except json.JSONDecodeError as e:
        raise InvalidInputError(f"Malformed JSON in '{filepath}': {e}") from e
    except OSError as e:
        raise FileIOError(f"Error reading file '{filepath}': {e}") from e


def write_json(filepath: str | Path, data: dict, indent: int = 2, sort_keys: bool = True) -> None:
    """
    Write data to a JSON file with deterministic output.

    Args:
        filepath: Path to the output JSON file
        data: Dictionary to write as JSON
        indent: Number of spaces for indentation (default: 2)
        sort_keys: Whether to sort keys alphabetically (default: True)

    Raises:
        FileIOError: If write operation fails
    """
    path = Path(filepath)
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
            f.write("\n")  # Add trailing newline for POSIX compliance
    except PermissionError as e:
        raise FileIOError(f"Permission denied writing to '{filepath}'") from e
    except OSError as e:
        raise FileIOError(f"Error writing to file '{filepath}': {e}") from e
    except (TypeError, ValueError) as e:
        raise FileIOError(f"Error serializing data to JSON: {e}") from e


def validate_json_structure(data: dict, required_keys: list[str]) -> list[str]:
    """
    Validate that required keys are present in a dictionary.

    Args:
        data: Dictionary to validate
        required_keys: List of required key names

    Returns:
        List of missing keys (empty list if all keys are present)
    """
    missing_keys = []
    for key in required_keys:
        if key not in data:
            missing_keys.append(key)
    return missing_keys
