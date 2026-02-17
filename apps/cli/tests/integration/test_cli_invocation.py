# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Integration tests for CLI invocation.
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from living_doc_cli.main import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def valid_input_data():
    """Create valid collector-gh input data."""
    return {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"},
            "run": {
                "run_id": "test-run",
                "run_attempt": "1",
                "actor": "test-actor",
                "workflow": "test-workflow",
                "ref": "main",
                "sha": "abc123",
            },
            "source": {
                "systems": ["github"],
                "repositories": ["owner/repo"],
                "organization": "owner",
                "enterprise": None,
            },
        },
        "issues": [
            {
                "number": 1,
                "title": "Test Issue",
                "state": "open",
                "labels": ["enhancement"],
                "html_url": "https://github.com/owner/repo/issues/1",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "body": "## Description\nThis is a test issue.\n\n## Acceptance Criteria\n- Criterion 1\n- Criterion 2",
            }
        ],
    }


def test_cli_invocation_success(runner, valid_input_data, tmp_path):
    """Test successful CLI invocation end-to-end with valid input."""
    # Create input file
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(valid_input_data, f)

    # Run CLI command
    result = runner.invoke(
        cli,
        [
            "normalize-issues",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--document-title",
            "Test Document",
            "--document-version",
            "1.0.0",
        ],
    )

    # Verify success
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
    assert "Successfully normalized" in result.output

    # Verify output file exists
    assert output_file.exists()

    # Verify output structure
    with open(output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    assert output_data["schema_version"] == "1.0"
    assert output_data["meta"]["document_title"] == "Test Document"
    assert output_data["meta"]["document_version"] == "1.0.0"
    assert len(output_data["content"]["user_stories"]) == 1

    story = output_data["content"]["user_stories"][0]
    assert story["id"] == "github:owner/repo#1"
    assert story["title"] == "Test Issue"
    assert "test issue" in story["sections"]["description"].lower()


def test_cli_invocation_missing_file(runner, tmp_path):
    """Test CLI with missing input file returns exit code 4 (wrapped as NormalizationError)."""
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    result = runner.invoke(cli, ["normalize-issues", "--input", str(input_file), "--output", str(output_file)])

    # Verify error exit code (FileIOError wrapped as NormalizationError by service)
    assert result.exit_code == 4
    assert "Error:" in result.output


def test_cli_invocation_bad_metadata(runner, tmp_path):
    """Test CLI with invalid metadata returns exit code 2."""
    # Create input with bad metadata
    input_data = {
        "metadata": {"generator": {"name": "unknown-adapter", "version": "1.0.0"}},
        "issues": [],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    result = runner.invoke(cli, ["normalize-issues", "--input", str(input_file), "--output", str(output_file)])

    # Verify adapter error exit code
    assert result.exit_code == 2
    assert "Adapter error:" in result.output


def test_cli_invocation_malformed_json(runner, tmp_path):
    """Test CLI with malformed JSON returns exit code 1."""
    input_file = tmp_path / "malformed.json"
    output_file = tmp_path / "output.json"

    # Write malformed JSON
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("{invalid json content")

    result = runner.invoke(cli, ["normalize-issues", "--input", str(input_file), "--output", str(output_file)])

    # Verify error exit code
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_cli_invocation_with_verbose(runner, valid_input_data, tmp_path):
    """Test CLI with verbose flag."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(valid_input_data, f)

    result = runner.invoke(
        cli, ["--verbose", "normalize-issues", "--input", str(input_file), "--output", str(output_file)]
    )

    # Should succeed
    assert result.exit_code == 0
    assert "Successfully normalized" in result.output


def test_cli_invocation_explicit_source(runner, valid_input_data, tmp_path):
    """Test CLI with explicit source adapter."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(valid_input_data, f)

    result = runner.invoke(
        cli,
        [
            "normalize-issues",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--source",
            "collector-gh",
        ],
    )

    # Should succeed
    assert result.exit_code == 0
    assert "Successfully normalized" in result.output
