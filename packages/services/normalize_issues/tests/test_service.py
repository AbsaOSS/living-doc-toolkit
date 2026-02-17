# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for service module.
"""

import json
from pathlib import Path

import pytest

from living_doc_core.errors import AdapterError, InvalidInputError, NormalizationError

from living_doc_service_normalize_issues.service import run_service


def test_run_service_valid_input(tmp_path):
    """Test full pipeline with valid input."""
    # Create input JSON file
    input_data = {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"},
            "run": {
                "run_id": "123",
                "run_attempt": "1",
                "actor": "testuser",
                "workflow": "test",
                "ref": "main",
                "sha": "abc123",
            },
            "source": {
                "systems": ["github"],
                "repositories": ["github:owner/repo"],
                "organization": "owner",
                "enterprise": None,
            },
        },
        "issues": [
            {
                "number": 123,
                "title": "Test Issue",
                "state": "open",
                "labels": ["enhancement"],
                "html_url": "https://github.com/owner/repo/issues/123",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "body": "## Description\nThis is a test issue.",
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    # Run service
    options = {"document_title": "Test Doc", "document_version": "1.0.0"}
    run_service(str(input_file), str(output_file), options)

    # Verify output file exists
    assert output_file.exists()

    # Load and verify output
    with open(output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    assert output_data["schema_version"] == "1.0"
    assert output_data["meta"]["document_title"] == "Test Doc"
    assert output_data["meta"]["document_version"] == "1.0.0"
    assert len(output_data["content"]["user_stories"]) == 1

    story = output_data["content"]["user_stories"][0]
    assert story["id"] == "github:owner/repo#123"
    assert story["title"] == "Test Issue"
    assert story["sections"]["description"] == "This is a test issue."


def test_run_service_missing_input_file(tmp_path):
    """Test error handling when input file is missing."""
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    options = {}

    with pytest.raises(Exception):  # Should raise FileIOError
        run_service(str(input_file), str(output_file), options)


def test_run_service_malformed_json(tmp_path):
    """Test error handling when input JSON is malformed."""
    input_file = tmp_path / "malformed.json"
    output_file = tmp_path / "output.json"

    # Write malformed JSON
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("{invalid json")

    options = {}

    with pytest.raises(InvalidInputError):
        run_service(str(input_file), str(output_file), options)


def test_run_service_adapter_detection_failure(tmp_path):
    """Test error handling when adapter detection fails."""
    # Create input with wrong metadata
    input_data = {
        "metadata": {"generator": {"name": "unknown-adapter", "version": "1.0.0"}},
        "issues": [],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    options = {}

    with pytest.raises(AdapterError):
        run_service(str(input_file), str(output_file), options)


def test_run_service_explicit_adapter(tmp_path):
    """Test using explicit adapter specification."""
    input_data = {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"},
            "run": {
                "run_id": None,
                "run_attempt": None,
                "actor": None,
                "workflow": None,
                "ref": None,
                "sha": None,
            },
            "source": {"systems": ["github"], "repositories": ["github:owner/repo"], "organization": None, "enterprise": None},
        },
        "issues": [
            {
                "number": 1,
                "title": "Test",
                "state": "open",
                "labels": [],
                "html_url": "https://github.com/owner/repo/issues/1",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "body": None,
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    options = {"source": "collector-gh"}
    run_service(str(input_file), str(output_file), options)

    assert output_file.exists()


def test_run_service_unsupported_adapter(tmp_path):
    """Test error handling for unsupported adapter."""
    input_data = {"metadata": {"generator": {"name": "some-adapter", "version": "1.0.0"}}, "issues": []}

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    options = {"source": "unsupported-adapter"}

    with pytest.raises(AdapterError) as exc_info:
        run_service(str(input_file), str(output_file), options)

    assert "Unsupported adapter" in str(exc_info.value)


def test_run_service_empty_items(tmp_path):
    """Test handling of input with no items."""
    input_data = {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"},
            "run": {
                "run_id": None,
                "run_attempt": None,
                "actor": None,
                "workflow": None,
                "ref": None,
                "sha": None,
            },
            "source": {"systems": ["github"], "repositories": ["github:owner/repo"], "organization": None, "enterprise": None},
        },
        "issues": [],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    options = {}
    run_service(str(input_file), str(output_file), options)

    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    assert len(output_data["content"]["user_stories"]) == 0
    assert output_data["meta"]["selection_summary"]["total_items"] == 0


def test_run_service_multiple_items(tmp_path):
    """Test processing multiple items."""
    input_data = {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"},
            "run": {
                "run_id": None,
                "run_attempt": None,
                "actor": None,
                "workflow": None,
                "ref": None,
                "sha": None,
            },
            "source": {"systems": ["github"], "repositories": ["github:owner/repo"], "organization": None, "enterprise": None},
        },
        "issues": [
            {
                "number": i,
                "title": f"Issue {i}",
                "state": "open",
                "labels": [],
                "html_url": f"https://github.com/owner/repo/issues/{i}",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "body": f"## Description\nIssue {i} content.",
            }
            for i in range(1, 4)
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    options = {}
    run_service(str(input_file), str(output_file), options)

    with open(output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    assert len(output_data["content"]["user_stories"]) == 3
    assert output_data["meta"]["selection_summary"]["total_items"] == 3
