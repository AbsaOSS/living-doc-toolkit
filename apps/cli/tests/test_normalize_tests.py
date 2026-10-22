# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `normalize-tests` command options, output, and failures."""

import logging

import pytest
from click.testing import CliRunner
from living_doc_service_normalize_tests import service
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_test_catalog import UiTestCatalogResult

from living_doc_cli.main import cli


@pytest.fixture(name="runner")
def _runner() -> CliRunner:
    return CliRunner()


def _errors(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("[ERROR]")]


def _read(path) -> UiTestCatalogResult:
    result = read_artifact(path, expected="ui-test-catalog")
    assert isinstance(result, UiTestCatalogResult)
    return result


def test_the_help_lists_only_input_and_output(runner):
    result = runner.invoke(cli, ["normalize-tests", "--help"])

    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--view" not in result.output
    assert "--verbose" not in result.output


@pytest.mark.parametrize("missing", ["--input", "--output"])
def test_input_and_output_are_required(runner, ui_tests, tmp_path, missing):
    options = {"--input": str(ui_tests), "--output": str(tmp_path / "ui-test-catalog.json")}
    del options[missing]
    args = ["normalize-tests", *(item for pair in options.items() for item in pair)]

    result = runner.invoke(cli, args)

    assert result.exit_code == 2
    assert f"Missing option '{missing}'" in result.output


def test_over_the_fixture_it_writes_a_valid_ui_test_catalog(runner, ui_tests, tmp_path):
    output = tmp_path / "out" / "ui-test-catalog.json"

    result = runner.invoke(cli, ["normalize-tests", f"--input={ui_tests}", f"--output={output}"])

    assert result.exit_code == 0, result.output
    catalog = _read(output)
    assert catalog.document.view == "inner"
    assert len(catalog.feature_files) == 2
    assert [(group.entity_id, len(group.scenarios)) for group in catalog.feature_files[0].linked_to_functionality] == [
        ("FUNC-001", 4)
    ]
    assert [(group.entity_id, len(group.scenarios)) for group in catalog.feature_files[1].linked_to_user_story] == [
        ("US-001", 2)
    ]
    assert not any(feature_file.unlinked for feature_file in catalog.feature_files)
    assert f"[INFO] normalize-tests - written: `{output}` (2 feature files, 6 scenarios)." in result.stderr.splitlines()


def test_a_missing_input_fails_with_one_missing_input_line_before_any_transform(runner, monkeypatch, tmp_path):
    def no_build(*_args, **_kwargs):
        raise AssertionError("the builder ran")

    monkeypatch.setattr(service, "build_ui_test_catalog", no_build)
    missing = tmp_path / "ui-tests.json"
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, ["normalize-tests", f"--input={missing}", f"--output={output}"])

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MISSING_INPUT] tests input {str(missing)!r}: no such file; check the path, or run the step "
        "that writes it first"
    ]
    assert not output.exists()


def test_a_field_loss_fails_with_one_line_and_writes_no_file(runner, monkeypatch, ui_tests, tmp_path):
    def raise_field_loss(_result):
        raise ContractError(Code.FIELD_LOSS, "lost")

    monkeypatch.setattr(service, "check_no_field_loss", raise_field_loss)
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, ["normalize-tests", f"--input={ui_tests}", f"--output={output}"])

    assert result.exit_code == 1
    assert _errors(result.stderr) == ["[ERROR] [FIELD_LOSS] lost"]
    assert not output.exists()


def test_an_output_that_cannot_be_written_fails_with_one_line(runner, ui_tests, tmp_path):
    output = tmp_path / "ui-test-catalog.json"
    output.mkdir()

    result = runner.invoke(cli, ["normalize-tests", f"--input={ui_tests}", f"--output={output}"])

    assert result.exit_code == 1
    errors = _errors(result.stderr)
    assert len(errors) == 1
    assert errors[0].startswith("[ERROR] normalize-tests - the output cannot be written: ")


@pytest.mark.parametrize("verbose", [True, False])
def test_verbose_before_the_command_name_turns_on_debug_logging(verbose, runner, ui_tests, tmp_path):
    args = ["--verbose", "normalize-tests", f"--input={ui_tests}", f"--output={tmp_path / 'out.json'}"]

    result = runner.invoke(cli, args) if verbose else runner.invoke(cli, args[1:])

    assert result.exit_code == 0, result.output
    assert logging.getLogger("living_doc").level == (logging.DEBUG if verbose else logging.INFO)
