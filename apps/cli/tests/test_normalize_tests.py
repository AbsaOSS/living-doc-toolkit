# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `normalize-tests` command options, output, and failures."""

import logging
from pathlib import Path

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


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def _args(doc_source: Path, ui_tests: Path, output: Path, *options: str) -> list[str]:
    return ["normalize-tests", f"--doc-input={doc_source}", f"--tests-input={ui_tests}", f"--output={output}", *options]


def test_the_help_lists_both_inputs_the_output_and_the_view(runner):
    result = runner.invoke(cli, ["normalize-tests", "--help"])

    assert result.exit_code == 0
    for option in ("--doc-input", "--tests-input", "--output", "--view"):
        assert option in result.output
    assert "[default: inner]" in result.output
    assert "--input " not in result.output
    assert "--verbose" not in result.output


@pytest.mark.parametrize("missing", ["--doc-input", "--tests-input", "--output"])
def test_the_inputs_and_the_output_are_required(runner, doc_source, ui_tests, tmp_path, missing):
    options = {
        "--doc-input": str(doc_source),
        "--tests-input": str(ui_tests),
        "--output": str(tmp_path / "ui-test-catalog.json"),
    }
    del options[missing]
    args = ["normalize-tests", *(item for pair in options.items() for item in pair)]

    result = runner.invoke(cli, args)

    assert result.exit_code == 2
    assert f"Missing option '{missing}'" in result.output


def test_over_the_fixture_pair_it_writes_a_valid_ui_test_catalog_in_the_inner_view(
    runner, doc_source, ui_tests, tmp_path
):
    output = tmp_path / "out" / "ui-test-catalog.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output))

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
    assert (
        f"[INFO] normalize-tests - written: `{output}` (inner view; 2 feature files, 6 scenarios)."
        in result.stderr.splitlines()
    )


def test_the_release_view_sets_document_view_and_keeps_a_deprecated_link(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, "--view", "release"))

    assert result.exit_code == 0, result.output
    catalog = _read(output)
    assert catalog.document.view == "release"
    links = [
        link
        for scenario in catalog.feature_files[1].linked_to_user_story[0].scenarios
        for link in scenario.acceptance_criteria
    ]
    assert [(link.id, link.state) for link in links] == [("US-001-01", "active"), ("US-001-04", "deprecated")]
    assert (
        f"[INFO] normalize-tests - written: `{output}` (release view; 2 feature files, 6 scenarios)."
        in result.stderr.splitlines()
    )


def test_a_missing_input_fails_with_one_missing_input_line_before_any_transform(
    runner, monkeypatch, ui_tests, tmp_path
):
    monkeypatch.setattr(service, "build_ui_test_catalog", _no_build)
    missing = tmp_path / "doc-source.json"
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, _args(missing, ui_tests, output))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MISSING_INPUT] documentation input {str(missing)!r}: no such file; check the path, or run the step "
        "that writes it first"
    ]
    assert not output.exists()


def test_a_tests_file_given_as_the_documentation_input_names_the_expected_contract(runner, ui_tests, tmp_path):
    # An old workflow passes the tests file as `input`, which is now the documentation input.
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, _args(ui_tests, ui_tests, output))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [CONTRACT_MISMATCH] documentation input {str(ui_tests)!r}: expected one of ['doc-source'], "
        "got 'ui-tests'"
    ]
    assert not output.exists()


def test_two_documentation_inputs_fail_with_one_line_each(runner, monkeypatch, doc_source, ui_tests, tmp_path):
    monkeypatch.setattr(service, "build_ui_test_catalog", _no_build)
    second = tmp_path / "second-doc-source.json"
    second.write_bytes(doc_source.read_bytes())
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, [*_args(doc_source, ui_tests, output), f"--doc-input={second}"])

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MULTIPLE_DOCUMENTATION_SOURCES] documentation input {str(path)!r}: one of 2 documentation files; "
        "a run reads exactly one, so pass one"
        for path in (doc_source, second)
    ]
    assert not output.exists()


def test_a_field_loss_fails_with_one_line_and_writes_no_file(runner, monkeypatch, doc_source, ui_tests, tmp_path):
    def raise_field_loss(_result):
        raise ContractError(Code.FIELD_LOSS, "lost")

    monkeypatch.setattr(service, "check_no_field_loss", raise_field_loss)
    output = tmp_path / "ui-test-catalog.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output))

    assert result.exit_code == 1
    assert _errors(result.stderr) == ["[ERROR] [FIELD_LOSS] lost"]
    assert not output.exists()


def test_an_output_that_cannot_be_written_fails_with_one_line(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "ui-test-catalog.json"
    output.mkdir()

    result = runner.invoke(cli, _args(doc_source, ui_tests, output))

    assert result.exit_code == 1
    errors = _errors(result.stderr)
    assert len(errors) == 1
    assert errors[0].startswith("[ERROR] normalize-tests - the output cannot be written: ")


@pytest.mark.parametrize("verbose", [True, False])
def test_verbose_before_the_command_name_turns_on_debug_logging(verbose, runner, doc_source, ui_tests, tmp_path):
    args = ["--verbose", *_args(doc_source, ui_tests, tmp_path / "out.json")]

    result = runner.invoke(cli, args) if verbose else runner.invoke(cli, args[1:])

    assert result.exit_code == 0, result.output
    assert logging.getLogger("living_doc").level == (logging.DEBUG if verbose else logging.INFO)
