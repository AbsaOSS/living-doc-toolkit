# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `coverage-matrix` command and its run-time field-loss check."""

import json
from pathlib import Path

import pytest
from living_doc_core.input_validation import InputValidationError, ValidatedInputs
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult, CoverageSummary
from living_doc_utilities.contracts.envelope import Run
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.testing import full_sample
from living_doc_utilities.contracts.ui_tests import AcLink

from living_doc_service_coverage_matrix import service
from living_doc_service_coverage_matrix.service import coverage_matrix

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "collector-gh"
DOC_SOURCE = FIXTURES / "doc-source.json"
UI_TESTS = FIXTURES / "ui-tests.json"
EXPECTED = Path(__file__).resolve().parent / "expected"


@pytest.fixture(name="sample_files")
def _sample_files(tmp_path) -> tuple[Path, Path]:
    documentation = tmp_path / "doc-source-sample.json"
    tests = tmp_path / "ui-tests-sample.json"
    write_artifact(full_sample("doc-source-v1.0.0"), documentation)
    write_artifact(full_sample("ui-tests-v1.0.0"), tests)
    return documentation, tests


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def _no_validation(*_args, **_kwargs):
    raise AssertionError("the shared input validation ran")


def _written(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["metadata"]["generated_at"] = "<masked>"
    return payload


def _every_criterion_planned(payload: dict) -> None:
    for root in ("user_stories", "features", "functionalities"):
        for entity in payload[root]:
            for criterion in entity["acceptance_criteria"]:
                criterion["state"] = "planned"
                criterion["removal_planned"] = None


def _problems(error: pytest.ExceptionInfo[InputValidationError]) -> list[tuple[Code | None, str]]:
    return [(problem.code, problem.message) for problem in error.value.problems]


def test_the_command_writes_the_committed_fixture_golden(tmp_path):
    output = tmp_path / "coverage-matrix.json"

    coverage_matrix([DOC_SOURCE], UI_TESTS, output)

    assert _written(output) == _written(EXPECTED / "coverage-matrix.json")


def test_the_release_view_differs_from_the_golden_only_in_document_view(tmp_path):
    output = tmp_path / "coverage-matrix.json"

    coverage_matrix([DOC_SOURCE], UI_TESTS, output, view="release")

    written = _written(output)
    assert written["document"] == {"view": "release"}
    assert {**written, "document": {"view": "inner"}} == _written(EXPECTED / "coverage-matrix.json")


def test_over_the_fixture_pair_the_matrix_counts_six_criteria(run_command):
    result = run_command()

    assert [entity.entity_id for entity in result.entities] == ["US-001", "FUNC-001", "FUNC-002"]
    assert result.summary == CoverageSummary(
        counted_acs=6, covered_acs=3, partially_covered_acs=1, not_covered_acs=2, coverage_pct=55.6
    )
    assert result.planned_summary.model_dump() == {"total": 2, "backlog": 1, "by_target_version": {"1.1.0": 1}}
    assert [warning.code for warning in result.warnings] == ["FEATURE_WITHOUT_FUNCTIONALITY", "UNRESOLVED_RELATION"]
    assert all(warning.context.startswith("source_input='doc-source-v1.0.0'") for warning in result.warnings)


@pytest.mark.parametrize("view", ["inner", "release"])
def test_over_the_utilities_full_samples_every_entity_and_summary_equals_the_coverage_matrix_samples(
    sample_files, run_command, view
):
    # The command raises FIELD_LOSS on a loss, and writes no file.
    result = run_command(*sample_files, view=view)
    sample = full_sample("coverage-matrix-v1.0.0")

    assert result.document.view == view
    assert [entity.entity_id for entity in result.entities] == [
        "US-001",
        "US-002",
        "US-010",
        "FUNC-001",
        "FUNC-002",
        "FUNC-003",
    ]
    # The sample lists its entities in another order, so it is compared by id: every row, aspect, keyword and summary.
    assert {entity.entity_id: entity for entity in result.entities} == {
        entity.entity_id: entity for entity in sample.entities
    }
    assert (
        result.summary
        == sample.summary
        == CoverageSummary(counted_acs=7, covered_acs=2, partially_covered_acs=1, not_covered_acs=4, coverage_pct=33.3)
    )
    assert result.planned_summary == sample.planned_summary
    assert result.warnings == []


def test_an_invalid_input_fails_before_the_builder_runs(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(InputValidationError) as error:
        coverage_matrix([DOC_SOURCE], tmp_path / "missing.json", output)

    assert [problem.code for problem in error.value.problems] == [Code.MISSING_INPUT]
    assert not output.exists()


def test_two_documentation_files_of_one_project_fail_with_one_problem_each(monkeypatch, tmp_path, changed_copy):
    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    second = changed_copy(DOC_SOURCE, lambda _payload: None, name="second-doc-source.json")
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(InputValidationError) as error:
        coverage_matrix([DOC_SOURCE, second], UI_TESTS, output)

    assert [problem.code for problem in error.value.problems] == [Code.MULTIPLE_DOCUMENTATION_SOURCES] * 2
    assert not output.exists()


def test_a_repeated_entity_id_and_a_repeated_criterion_id_each_fail_with_one_problem_listing_every_place(
    monkeypatch, tmp_path, changed_copy
):
    def repeat_ids(payload):
        payload["functionalities"].append(payload["functionalities"][1])
        criteria = payload["user_stories"][0]["acceptance_criteria"]
        criteria.append(criteria[0])

    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    documentation = changed_copy(DOC_SOURCE, repeat_ids)

    with pytest.raises(InputValidationError) as error:
        coverage_matrix([documentation], UI_TESTS, tmp_path / "coverage-matrix.json")

    assert _problems(error) == [
        (
            Code.DUPLICATE_ENTITY_ID,
            "entity id 'FUNC-002' at functionalities[1], functionalities[2]; one id names one entity, so renumber "
            "all but one at the source",
        ),
        (
            Code.DUPLICATE_AC_ID,
            "acceptance criterion id 'US-001-01' at user_stories[0].acceptance_criteria[0], "
            "user_stories[0].acceptance_criteria[4]; one id names one criterion of its entity, so renumber all but "
            "one at the source",
        ),
    ]


@pytest.mark.parametrize("doc_inputs", [str(DOC_SOURCE), DOC_SOURCE])
def test_one_documentation_path_in_place_of_a_sequence_is_refused_before_validation(monkeypatch, tmp_path, doc_inputs):
    monkeypatch.setattr(service, "validate_inputs", _no_validation)
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(TypeError) as error:
        coverage_matrix(doc_inputs, UI_TESTS, output)

    assert str(error.value) == (
        f"coverage-matrix - doc_inputs is one path, {str(DOC_SOURCE)!r}; pass a sequence of paths"
    )
    assert not output.exists()


@pytest.mark.parametrize("role", ["documentation", "tests"])
def test_a_validation_that_returns_no_input_for_a_role_stops_before_any_transform(
    monkeypatch, tmp_path, documentation, ui_tests, role
):
    # A defect in the shared input validation, which returns an input for every role the command takes.
    inputs = (
        ValidatedInputs(tests=ui_tests) if role == "documentation" else ValidatedInputs(documentation=documentation)
    )
    monkeypatch.setattr(service, "validate_inputs", lambda *_args: inputs)
    monkeypatch.setattr(service, "build_coverage_matrix", _no_build)
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(RuntimeError, match=f"^coverage-matrix - the shared input validation returned no {role} input"):
        coverage_matrix([DOC_SOURCE], UI_TESTS, output)

    assert not output.exists()


def test_the_ci_run_is_recorded_and_each_input_keeps_its_own_run(documentation, ui_tests, tmp_path, monkeypatch):
    documentation_run = Run(run_id="101", run_attempt="1", actor="collector", workflow="collect", ref="refs/tags/v1")
    tests_run = Run(run_id="102", run_attempt="3", actor="collector", workflow="collect-tests")
    documentation_path = tmp_path / "doc-source.json"
    tests_path = tmp_path / "ui-tests.json"
    for model, run, path in ((documentation, documentation_run, documentation_path), (ui_tests, tests_run, tests_path)):
        write_artifact(model.model_copy(update={"metadata": model.metadata.model_copy(update={"run": run})}), path)
    monkeypatch.setenv("GITHUB_RUN_ID", "4242")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setenv("GITHUB_ACTOR", "octocat")
    monkeypatch.setenv("GITHUB_WORKFLOW", "docs")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/master")
    monkeypatch.setenv("GITHUB_SHA", "3f2c1ab")

    result = coverage_matrix([documentation_path], tests_path, tmp_path / "coverage-matrix.json")

    assert result.metadata.run == Run(
        run_id="4242", run_attempt="2", actor="octocat", workflow="docs", ref="refs/heads/master", sha="3f2c1ab"
    )
    assert [entry.run for entry in result.metadata.source_inputs] == [documentation_run, tests_run]


def test_a_documentation_file_whose_criteria_are_all_planned_gets_its_matrix_without_field_loss(
    changed_copy, run_command
):
    documentation = changed_copy(DOC_SOURCE, _every_criterion_planned)

    result = run_command(documentation)

    assert [entity.entity_id for entity in result.entities] == ["US-001", "FUNC-001", "FUNC-002"]
    assert all(not entity.acceptance_criteria for entity in result.entities)
    assert result.summary.counted_acs == 0
    assert result.summary.coverage_pct is None
    assert result.planned_summary.model_dump() == {
        "total": 8,
        "backlog": 1,
        "by_target_version": {"1.0.0": 6, "1.1.0": 1},
    }


def test_a_link_to_an_in_review_criterion_warns_and_the_matrix_is_still_written(
    documentation, ui_tests, tmp_path, run_command
):
    user_story = documentation.user_stories[0]
    criteria = [*user_story.acceptance_criteria]
    criteria[1] = criteria[1].model_copy(update={"state": "in_review"})
    in_review = documentation.model_copy(
        update={"user_stories": [user_story.model_copy(update={"acceptance_criteria": criteria})]}
    )
    scenario = ui_tests.scenarios[4]
    linked = scenario.model_copy(
        update={"acceptance_criteria": [*scenario.acceptance_criteria, AcLink(id="US-001-02")]}
    )
    tests = ui_tests.model_copy(update={"scenarios": [*ui_tests.scenarios[:4], linked, ui_tests.scenarios[5]]})
    documentation_path = tmp_path / "doc-source.json"
    tests_path = tmp_path / "ui-tests.json"
    write_artifact(in_review, documentation_path)
    write_artifact(tests, tests_path)

    result = run_command(documentation_path, tests_path)

    assert [row.ac_id for row in result.entities[0].acceptance_criteria] == ["US-001-01", "US-001-04"]
    assert [(warning.code, warning.ac_id, warning.entity_id, warning.context) for warning in result.warnings[2:]] == [
        ("IN_REVIEW_AC_HAS_TESTS", "US-001-02", "US-001", f"scenario_id={scenario.scenario_id!r}")
    ]


def _with_rows(result: CoverageMatrixResult, change: dict) -> CoverageMatrixResult:
    """The result with `change` applied to every row; `model_copy` skips the row checks the write would run."""
    entities = [
        entity.model_copy(
            update={"acceptance_criteria": [row.model_copy(update=change) for row in entity.acceptance_criteria]}
        )
        for entity in result.entities
    ]
    return result.model_copy(update={"entities": entities})


def _without_aspects(result: CoverageMatrixResult) -> CoverageMatrixResult:
    return _with_rows(result, {"aspects": [], "keyword": None})


def _without_keywords(result: CoverageMatrixResult) -> CoverageMatrixResult:
    return _with_rows(result, {"keyword": None})


def _without_rows(result: CoverageMatrixResult) -> CoverageMatrixResult:
    entities = [
        entity.model_copy(update={"acceptance_criteria": [], "summary": CoverageSummary.from_rows([])})
        for entity in result.entities
    ]
    return result.model_copy(update={"entities": entities, "summary": CoverageSummary.from_rows([])})


def _without_titles(result: CoverageMatrixResult) -> CoverageMatrixResult:
    return result.model_copy(
        update={"entities": [entity.model_copy(update={"title": ""}) for entity in result.entities]}
    )


@pytest.mark.parametrize(
    ("drop", "lost"),
    [
        (_without_rows, "user_stories[].acceptance_criteria[].id"),
        (_without_titles, "functionalities[].title"),
        # The fixture declares its aspects and its keyword on FUNC-001 only.
        (_without_aspects, "functionalities[].acceptance_criteria[].aspect[]"),
        (_without_aspects, "functionalities[].acceptance_criteria[].placeholder_values"),
        (_without_keywords, "functionalities[].acceptance_criteria[].placeholder_values"),
    ],
)
def test_a_builder_that_drops_a_mapped_field_fails_with_field_loss_and_writes_no_file(
    monkeypatch, tmp_path, drop, lost
):
    build = service.build_coverage_matrix
    monkeypatch.setattr(service, "build_coverage_matrix", lambda *args, **kwargs: drop(build(*args, **kwargs)))
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(ContractError) as error:
        coverage_matrix([DOC_SOURCE], UI_TESTS, output)

    assert error.value.code is Code.FIELD_LOSS
    assert f"'{lost}' had occupancy" in error.value.message
    assert not output.exists()


@pytest.mark.parametrize(
    ("drop", "lost"),
    [
        (_without_aspects, "user_stories[].acceptance_criteria[].aspect[]"),
        (_without_keywords, "user_stories[].acceptance_criteria[].placeholder_values"),
    ],
)
def test_over_the_full_samples_a_builder_that_drops_user_story_aspects_fails_with_field_loss(
    monkeypatch, sample_files, tmp_path, drop, lost
):
    # The fixture declares aspects on a Functionality only; the full samples declare them on User Stories too.
    build = service.build_coverage_matrix
    monkeypatch.setattr(service, "build_coverage_matrix", lambda *args, **kwargs: drop(build(*args, **kwargs)))
    documentation, tests = sample_files
    output = tmp_path / "coverage-matrix.json"

    with pytest.raises(ContractError) as error:
        coverage_matrix([documentation], tests, output)

    assert error.value.code is Code.FIELD_LOSS
    assert f"'{lost}' had occupancy" in error.value.message
    assert not output.exists()


def test_field_loss_leaves_an_existing_output_untouched(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "check_no_field_loss", lambda _result: _raise_field_loss())
    output = tmp_path / "coverage-matrix.json"
    output.write_text("previous run", encoding="utf-8")

    with pytest.raises(ContractError):
        coverage_matrix([DOC_SOURCE], UI_TESTS, output)

    assert output.read_text(encoding="utf-8") == "previous run"


def _raise_field_loss() -> None:
    raise ContractError(Code.FIELD_LOSS, "lost")
