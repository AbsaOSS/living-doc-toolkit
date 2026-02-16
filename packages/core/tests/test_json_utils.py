# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for JSON utilities.
"""

import json
import tempfile
from pathlib import Path

import pytest

from living_doc_core.errors import FileIOError, InvalidInputError
from living_doc_core.json_utils import read_json, validate_json_structure, write_json


def test_read_json_with_valid_file():
    """Test reading a valid JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_data = {"key": "value", "number": 42}
        json.dump(test_data, f)
        temp_path = f.name

    try:
        result = read_json(temp_path)
        assert result == test_data
    finally:
        Path(temp_path).unlink()


def test_read_json_with_malformed_json():
    """Test that reading malformed JSON raises InvalidInputError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{invalid json")
        temp_path = f.name

    try:
        with pytest.raises(InvalidInputError) as exc_info:
            read_json(temp_path)
        assert "Malformed JSON" in str(exc_info.value)
    finally:
        Path(temp_path).unlink()


def test_read_json_with_non_existent_file():
    """Test that reading non-existent file raises FileIOError."""
    non_existent = "/tmp/non_existent_file_12345.json"
    with pytest.raises(FileIOError) as exc_info:
        read_json(non_existent)
    assert "not found" in str(exc_info.value)


def test_write_json_with_valid_data():
    """Test writing valid data to JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.json"
        test_data = {"key": "value", "number": 42}

        write_json(output_path, test_data)

        # Verify file was written
        assert output_path.exists()

        # Verify content
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            loaded_data = json.loads(content)
            assert loaded_data == test_data


def test_write_json_round_trip():
    """Test that write then read produces identical data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "roundtrip.json"
        original_data = {
            "name": "test",
            "items": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Write and read back
        write_json(output_path, original_data)
        loaded_data = read_json(output_path)

        assert loaded_data == original_data


def test_write_json_with_invalid_path():
    """Test that writing to invalid path raises FileIOError."""
    # Try to write to a directory that doesn't exist with no permission to create
    invalid_path = "/root/nonexistent/impossible/path.json"
    with pytest.raises(FileIOError) as exc_info:
        write_json(invalid_path, {"key": "value"})
    assert "Error writing" in str(exc_info.value) or "Permission denied" in str(exc_info.value)


def test_write_json_deterministic_output():
    """Test that write_json produces deterministic output with sort_keys=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "deterministic.json"
        test_data = {"zebra": 1, "alpha": 2, "beta": 3}

        write_json(output_path, test_data, sort_keys=True)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Keys should be sorted alphabetically
            assert content.index("alpha") < content.index("beta")
            assert content.index("beta") < content.index("zebra")


def test_write_json_respects_indent():
    """Test that write_json respects the indent parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "indented.json"
        test_data = {"key": "value"}

        write_json(output_path, test_data, indent=4)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Should have 4-space indentation
            assert "    " in content


def test_validate_json_structure_with_all_keys_present():
    """Test validate_json_structure when all required keys are present."""
    data = {"key1": "value1", "key2": "value2", "key3": "value3"}
    required = ["key1", "key2"]
    missing = validate_json_structure(data, required)
    assert missing == []


def test_validate_json_structure_with_missing_keys():
    """Test validate_json_structure when keys are missing."""
    data = {"key1": "value1"}
    required = ["key1", "key2", "key3"]
    missing = validate_json_structure(data, required)
    assert sorted(missing) == ["key2", "key3"]


def test_validate_json_structure_with_empty_required():
    """Test validate_json_structure with no required keys."""
    data = {"key": "value"}
    required = []
    missing = validate_json_structure(data, required)
    assert missing == []


def test_validate_json_structure_with_empty_data():
    """Test validate_json_structure with empty data dict."""
    data = {}
    required = ["key1", "key2"]
    missing = validate_json_structure(data, required)
    assert sorted(missing) == ["key1", "key2"]


def test_write_json_creates_parent_directories():
    """Test that write_json creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "nested" / "path" / "output.json"
        test_data = {"key": "value"}

        write_json(output_path, test_data)

        assert output_path.exists()
        assert read_json(output_path) == test_data
