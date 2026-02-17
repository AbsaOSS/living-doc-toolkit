# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for CLI commands.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from living_doc_core.errors import (
    AdapterError,
    FileIOError,
    InvalidInputError,
    NormalizationError,
    SchemaValidationError,
)
from living_doc_cli.main import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that --help displays usage information."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Living Documentation Toolkit CLI" in result.output
    assert "normalize-issues" in result.output


def test_cli_version(runner):
    """Test that --version displays version information."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_normalize_issues_help(runner):
    """Test that normalize-issues --help displays usage information."""
    result = runner.invoke(cli, ["normalize-issues", "--help"])
    assert result.exit_code == 0
    assert "normalize-issues" in result.output
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--source" in result.output
    assert "--document-title" in result.output
    assert "--document-version" in result.output
    assert "--verbose" in result.output


def test_normalize_issues_missing_required_args(runner):
    """Test that missing required arguments shows error."""
    result = runner.invoke(cli, ["normalize-issues"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "Error" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_success(mock_run_service, runner):
    """Test successful execution of normalize-issues command."""
    mock_run_service.return_value = None

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 0
    assert "Successfully normalized" in result.output
    mock_run_service.assert_called_once()

    # Verify options passed to service
    call_args = mock_run_service.call_args
    assert call_args[0][0] == "input.json"
    assert call_args[0][1] == "output.json"
    options = call_args[0][2]
    assert options["verbose"] is False
    assert options["source"] == "auto"


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_with_all_options(mock_run_service, runner):
    """Test normalize-issues with all optional arguments."""
    mock_run_service.return_value = None

    result = runner.invoke(
        cli,
        [
            "normalize-issues",
            "--input",
            "input.json",
            "--output",
            "output.json",
            "--source",
            "collector-gh",
            "--document-title",
            "Test Document",
            "--document-version",
            "1.0.0",
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    mock_run_service.assert_called_once()

    # Verify all options
    call_args = mock_run_service.call_args
    options = call_args[0][2]
    assert options["verbose"] is True
    assert options["source"] == "collector-gh"
    assert options["document_title"] == "Test Document"
    assert options["document_version"] == "1.0.0"


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_global_verbose(mock_run_service, runner):
    """Test that global --verbose flag is passed to command."""
    mock_run_service.return_value = None

    result = runner.invoke(cli, ["--verbose", "normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 0
    mock_run_service.assert_called_once()

    # Verify verbose flag was passed
    call_args = mock_run_service.call_args
    options = call_args[0][2]
    assert options["verbose"] is True


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_local_verbose_overrides_global(mock_run_service, runner):
    """Test that local --verbose overrides global."""
    mock_run_service.return_value = None

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json", "--verbose"])

    assert result.exit_code == 0
    mock_run_service.assert_called_once()

    call_args = mock_run_service.call_args
    options = call_args[0][2]
    assert options["verbose"] is True


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_invalid_input_error(mock_run_service, runner):
    """Test exit code 1 for InvalidInputError."""
    mock_run_service.side_effect = InvalidInputError("File 'doc-issues.json' not found")

    result = runner.invoke(cli, ["normalize-issues", "--input", "missing.json", "--output", "output.json"])

    assert result.exit_code == 1
    assert "Invalid input:" in result.output
    assert "File 'doc-issues.json' not found" in result.output
    assert "Ensure --input points to a valid file" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_adapter_error(mock_run_service, runner):
    """Test exit code 2 for AdapterError."""
    mock_run_service.side_effect = AdapterError("No compatible adapter found for input")

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 2
    assert "Adapter error:" in result.output
    assert "No compatible adapter found for input" in result.output
    assert "Check metadata.generator.name field" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_schema_validation_error(mock_run_service, runner):
    """Test exit code 3 for SchemaValidationError."""
    mock_run_service.side_effect = SchemaValidationError("Output schema validation failed")

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 3
    assert "Schema validation failed:" in result.output
    assert "Output schema validation failed" in result.output
    assert "Review the output schema requirements" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_normalization_error(mock_run_service, runner):
    """Test exit code 4 for NormalizationError."""
    mock_run_service.side_effect = NormalizationError("Parsing failure during normalization")

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 4
    assert "Normalization failed:" in result.output
    assert "Parsing failure during normalization" in result.output
    assert "Check input data format and content" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_file_io_error(mock_run_service, runner):
    """Test exit code 5 for FileIOError."""
    mock_run_service.side_effect = FileIOError("Cannot write to output file")

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 5
    assert "File I/O error:" in result.output
    assert "Cannot write to output file" in result.output
    assert "Ensure output directory exists and is writable" in result.output


@patch("living_doc_cli.commands.normalize_issues.run_service")
def test_normalize_issues_unexpected_error(mock_run_service, runner):
    """Test exit code 1 for unexpected errors."""
    mock_run_service.side_effect = RuntimeError("Unexpected failure")

    result = runner.invoke(cli, ["normalize-issues", "--input", "input.json", "--output", "output.json"])

    assert result.exit_code == 1
    assert "Unexpected error:" in result.output
    assert "Unexpected failure" in result.output
