# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `coverage-matrix` command: its options, the file it writes, the `--fail-under` gate, and failures."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from living_doc_service_coverage_matrix import service
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.io import read_artifact, write_artifact
from living_doc_utilities.contracts.ui_tests import AcLink, UITestsResult

from living_doc_cli.main import cli


@pytest.fixture(name="runner")
def _runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(name="changed_copy")
def _changed_copy(tmp_path) -> Callable[..., Path]:
    def changed_copy(fixture: Path, change: Callable[[dict[str, Any]], object], name: str | None = None) -> Path:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        change(payload)
        path = tmp_path / (name or fixture.name)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return changed_copy


def _errors(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("[ERROR]")]


def _read(path) -> CoverageMatrixResult:
    result = read_artifact(path, expected="coverage-matrix")
    assert isinstance(result, CoverageMatrixResult)
    return result


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def _every_criterion_planned(payload: dict) -> None:
    for root in ("user_stories", "features", "functionalities"):
        for entity in payload[root]:
            for criterion in entity["acceptance_criteria"]:
                criterion["state"] = "planned"
                criterion["removal_planned"] = None


def _args(doc_source: Path, ui_tests: Path, output: Path, *options: str) -> list[str]:
    return ["coverage-matrix", f"--doc-input={doc_source}", f"--tests-input={ui_tests}", f"--output={output}", *options]


def test_the_help_lists_the_options_and_names_no_retired_artifact(runner):
    result = runner.invoke(cli, ["coverage-matrix", "--help"])

    assert result.exit_code == 0
    for option in ("--doc-input", "--tests-input", "--output", "--view", "--fail-under"):
        assert option in result.output
    assert "[default: inner]" in result.output
    assert "--verbose" not in result.output
    for retired in ("doc-issues.json", "work-items.json", "normalize-issues", "meta.audit", "items[]"):
        assert retired not in result.output


@pytest.mark.parametrize("missing", ["--doc-input", "--tests-input", "--output"])
def test_the_inputs_and_the_output_are_required(runner, doc_source, ui_tests, tmp_path, missing):
    options = {
        "--doc-input": str(doc_source),
        "--tests-input": str(ui_tests),
        "--output": str(tmp_path / "coverage-matrix.json"),
    }
    del options[missing]

    result = runner.invoke(cli, ["coverage-matrix", *(item for pair in options.items() for item in pair)])

    assert result.exit_code == 2
    assert f"Missing option '{missing}'" in result.output


def test_over_the_fixture_pair_it_writes_a_valid_matrix_in_the_inner_view(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "out" / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output))

    assert result.exit_code == 0, result.output
    matrix = _read(output)
    assert matrix.document.view == "inner"
    assert [entity.entity_id for entity in matrix.entities] == ["US-001", "FUNC-001", "FUNC-002"]
    summary = matrix.summary
    assert (summary.counted_acs, summary.covered_acs, summary.not_covered_acs, summary.coverage_pct) == (6, 3, 2, 55.6)
    assert (
        f"[INFO] coverage-matrix - written: `{output}` (inner view; 6 counted acceptance criteria, 3 covered, 55.6%)."
        in result.stderr.splitlines()
    )


def test_the_release_view_sets_document_view_and_counts_the_same(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, "--view", "release"))

    assert result.exit_code == 0, result.output
    matrix = _read(output)
    assert matrix.document.view == "release"
    assert (matrix.summary.counted_acs, matrix.summary.coverage_pct) == (6, 55.6)


def test_fail_under_at_the_coverage_percentage_passes(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, "--fail-under=55.6"))

    assert result.exit_code == 0, result.output
    assert _errors(result.stderr) == []
    assert output.exists()


def test_fail_under_just_above_the_coverage_percentage_fails_with_one_line_and_keeps_the_file(
    runner, doc_source, ui_tests, tmp_path
):
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, "--fail-under=55.7"))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        "[ERROR] coverage-matrix - the coverage percentage, 55.6, is below --fail-under 55.7."
    ]
    assert _read(output).summary.coverage_pct == 55.6


def test_a_link_to_an_in_review_criterion_is_a_warning_in_the_file_and_the_run_succeeds(
    runner, doc_source, ui_tests, tmp_path
):
    documentation = read_artifact(doc_source, expected="doc-source")
    tests = read_artifact(ui_tests, expected="ui-tests")
    assert isinstance(documentation, DocSourceResult)
    assert isinstance(tests, UITestsResult)
    user_story = documentation.user_stories[0]
    criteria = [*user_story.acceptance_criteria]
    criteria[1] = criteria[1].model_copy(update={"state": "in_review"})
    documentation_path = tmp_path / "doc-source.json"
    write_artifact(
        documentation.model_copy(
            update={"user_stories": [user_story.model_copy(update={"acceptance_criteria": criteria})]}
        ),
        documentation_path,
    )
    scenario = tests.scenarios[4]
    tests.scenarios[4] = scenario.model_copy(
        update={"acceptance_criteria": [*scenario.acceptance_criteria, AcLink(id="US-001-02")]}
    )
    tests_path = tmp_path / "ui-tests.json"
    write_artifact(tests, tests_path)
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(documentation_path, tests_path, output, "--fail-under=0"))

    assert result.exit_code == 0, result.output
    # The warning is the file's: no command logs one.
    assert [line for line in result.stderr.splitlines() if not line.startswith("[INFO]")] == []
    matrix = _read(output)
    assert [(warning.code, warning.ac_id) for warning in matrix.warnings[2:]] == [
        ("IN_REVIEW_AC_HAS_TESTS", "US-001-02")
    ]
    assert "US-001-02" not in [row.ac_id for row in matrix.entities[0].acceptance_criteria]


def test_a_matrix_with_no_coverage_percentage_fails_any_fail_under_and_keeps_the_file(
    runner, changed_copy, doc_source, ui_tests, tmp_path
):
    documentation = changed_copy(doc_source, _every_criterion_planned)
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(documentation, ui_tests, output, "--fail-under=0"))

    assert result.exit_code == 1
    assert (
        f"[INFO] coverage-matrix - written: `{output}` (inner view; 0 counted acceptance criteria, 0 covered, "
        "no coverage percentage)." in result.stderr.splitlines()
    )
    assert _errors(result.stderr) == [
        "[ERROR] coverage-matrix - no acceptance criterion is counted, so the matrix has no coverage percentage, "
        "which fails --fail-under 0."
    ]
    assert _read(output).summary.coverage_pct is None


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_a_fail_under_that_is_not_a_finite_number_is_a_usage_error_and_writes_no_file(
    runner, doc_source, ui_tests, tmp_path, value
):
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, f"--fail-under={value}"))

    assert result.exit_code == 2
    assert f"Invalid value for '--fail-under': {float(value)} is not a finite number." in result.output
    assert not output.exists()


def test_two_documentation_files_of_one_project_fail_with_one_line_each_before_any_transform(
    runner, monkeypatch, changed_copy, doc_source, ui_tests, tmp_path
):
    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    second = changed_copy(doc_source, lambda _payload: None, name="second-doc-source.json")
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, [*_args(doc_source, ui_tests, output), f"--doc-input={second}"])

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MULTIPLE_DOCUMENTATION_SOURCES] documentation input {str(path)!r}: one of 2 documentation files; "
        "a run reads exactly one, so pass one"
        for path in (doc_source, second)
    ]
    assert not output.exists()


def test_a_repeated_entity_id_fails_with_one_line_listing_every_place(
    runner, monkeypatch, changed_copy, doc_source, ui_tests, tmp_path
):
    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    documentation = changed_copy(doc_source, lambda payload: payload["user_stories"].append(payload["user_stories"][0]))

    result = runner.invoke(cli, _args(documentation, ui_tests, tmp_path / "coverage-matrix.json"))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [DUPLICATE_ENTITY_ID] documentation input {str(documentation)!r}: entity id 'US-001' at "
        "user_stories[0], user_stories[1]; one id names one entity, so renumber all but one at the source"
    ]


def test_a_repeated_criterion_id_fails_with_one_line_listing_every_place(
    runner, monkeypatch, changed_copy, doc_source, ui_tests, tmp_path
):
    def repeat_criterion(payload):
        criteria = payload["functionalities"][0]["acceptance_criteria"]
        criteria.append(criteria[1])

    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    documentation = changed_copy(doc_source, repeat_criterion)

    result = runner.invoke(cli, _args(documentation, ui_tests, tmp_path / "coverage-matrix.json"))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [DUPLICATE_AC_ID] documentation input {str(documentation)!r}: acceptance criterion id "
        "'FUNC-001-02' at functionalities[0].acceptance_criteria[1], functionalities[0].acceptance_criteria[3]; one id "
        "names one criterion of its entity, so renumber all but one at the source"
    ]


def test_a_missing_tests_input_fails_with_one_missing_input_line(runner, doc_source, tmp_path):
    missing = tmp_path / "ui-tests.json"
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, missing, output))

    assert result.exit_code == 1
    assert _errors(result.stderr) == [
        f"[ERROR] [MISSING_INPUT] tests input {str(missing)!r}: no such file; check the path, or run the step "
        "that writes it first"
    ]
    assert not output.exists()


def test_a_field_loss_fails_with_one_line_and_writes_no_file(runner, monkeypatch, doc_source, ui_tests, tmp_path):
    def raise_field_loss(_result):
        raise ContractError(Code.FIELD_LOSS, "lost")

    monkeypatch.setattr(service, "check_no_field_loss", raise_field_loss)
    output = tmp_path / "coverage-matrix.json"

    result = runner.invoke(cli, _args(doc_source, ui_tests, output, "--fail-under=0"))

    assert result.exit_code == 1
    assert _errors(result.stderr) == ["[ERROR] [FIELD_LOSS] lost"]
    assert not output.exists()


def test_an_output_that_cannot_be_written_fails_with_one_line(runner, doc_source, ui_tests, tmp_path):
    output = tmp_path / "coverage-matrix.json"
    output.mkdir()

    result = runner.invoke(cli, _args(doc_source, ui_tests, output))

    assert result.exit_code == 1
    errors = _errors(result.stderr)
    assert len(errors) == 1
    assert errors[0].startswith("[ERROR] coverage-matrix - the output cannot be written: ")


@pytest.mark.parametrize("verbose", [True, False])
def test_verbose_before_the_command_name_turns_on_debug_logging(verbose, runner, doc_source, ui_tests, tmp_path):
    args = ["--verbose", *_args(doc_source, ui_tests, tmp_path / "out.json")]

    result = runner.invoke(cli, args) if verbose else runner.invoke(cli, args[1:])

    assert result.exit_code == 0, result.output
    assert logging.getLogger("living_doc").level == (logging.DEBUG if verbose else logging.INFO)
