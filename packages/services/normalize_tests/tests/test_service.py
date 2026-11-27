# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `normalize-tests` command and its run-time field-loss check."""

import json
from pathlib import Path

import pytest
from living_doc_core.input_validation import InputValidationError, ValidatedInputs
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import ContractWarning, Run
from living_doc_utilities.contracts.io import read_artifact, write_artifact
from living_doc_utilities.contracts.testing import full_sample
from living_doc_utilities.contracts.ui_tests import AcLink

from living_doc_service_normalize_tests import service
from living_doc_service_normalize_tests.lineage import (
    FUNCTIONALITY_SCENARIO_ROOT,
    SCENARIO_PATHS,
    UNLINKED_SCENARIO_ROOT,
    USER_STORY_SCENARIO_ROOT,
)
from living_doc_service_normalize_tests.service import normalize_tests

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "collector-gh"
DOC_SOURCE = FIXTURES / "doc-source.json"
UI_TESTS = FIXTURES / "ui-tests.json"
EXPECTED = Path(__file__).resolve().parent / "expected"


@pytest.fixture(name="sample_pair")
def _sample_pair(tmp_path) -> tuple[Path, Path]:
    doc_path = tmp_path / "doc-source-sample.json"
    tests_path = tmp_path / "ui-tests-sample.json"
    write_artifact(full_sample("doc-source-v1.0.0"), doc_path)
    write_artifact(full_sample("ui-tests-v1.0.0"), tests_path)
    return doc_path, tests_path


def _no_build(*_args, **_kwargs):
    raise AssertionError("the builder ran")


def _masked(payload: dict) -> dict:
    payload["metadata"]["generated_at"] = "<masked>"
    return payload


def _written(path: Path) -> dict:
    return _masked(json.loads(path.read_text(encoding="utf-8")))


def _one_scenario_linking(ui_tests, tmp_path, *links: AcLink) -> Path:
    scenario = ui_tests.scenarios[4].model_copy(update={"acceptance_criteria": list(links)})
    path = tmp_path / "one-scenario-ui-tests.json"
    write_artifact(ui_tests.model_copy(update={"scenarios": [scenario]}), path)
    return path


def test_the_command_writes_the_committed_fixture_golden(tmp_path):
    output = tmp_path / "ui-test-catalog.json"

    normalize_tests([DOC_SOURCE], UI_TESTS, output)

    assert _written(output) == _written(EXPECTED / "ui-test-catalog.json")


def test_over_the_fixture_the_release_view_differs_from_the_golden_only_in_document_view(tmp_path):
    output = tmp_path / "ui-test-catalog.json"

    normalize_tests([DOC_SOURCE], UI_TESTS, output, view="release")

    expected = _written(EXPECTED / "ui-test-catalog.json")
    expected["document"]["view"] = "release"
    assert _written(output) == expected


def test_the_fixture_catalog_has_two_files_and_aggregates_functionality_fields(run_command):
    result = run_command(DOC_SOURCE, UI_TESTS)

    assert result.document.view == "inner"
    assert len(result.feature_files) == 2
    assert result.feature_files[0].linked_to_functionality[0].entity_id == "FUNC-001"
    assert len(result.feature_files[0].linked_to_functionality[0].scenarios) == 4
    assert result.feature_files[1].linked_to_user_story[0].entity_id == "US-001"
    assert len(result.feature_files[1].linked_to_user_story[0].scenarios) == 2
    assert not any(feature_file.unlinked for feature_file in result.feature_files)
    occupancy = result.metadata.stats.field_occupancy
    assert occupancy[f"{USER_STORY_SCENARIO_ROOT}acceptance_criteria[].aspect"] == 0
    assert occupancy[f"{FUNCTIONALITY_SCENARIO_ROOT}acceptance_criteria[].aspect"] == 4
    assert occupancy[f"{USER_STORY_SCENARIO_ROOT}acceptance_criteria[].state"] == 2


def test_the_command_records_both_inputs_and_copies_the_tests_source(ui_tests, run_command):
    result = run_command(DOC_SOURCE, UI_TESTS)

    assert result.metadata.source == ui_tests.metadata.source
    assert [entry.schema_version for entry in result.metadata.source_inputs] == [
        "doc-source-v1.0.0",
        "ui-tests-v1.0.0",
    ]
    cardinality = result.metadata.stats.cardinality
    assert (cardinality.sources_configured, cardinality.sources_failed) == (0, 0)
    assert (cardinality.unresolved_refs, cardinality.entities_skipped) == (0, 0)


def test_the_producer_uses_the_toolkit_identity_and_keeps_build_null(run_command):
    producer = run_command(DOC_SOURCE, UI_TESTS).metadata.producer

    assert producer.name == "AbsaOSS/living-doc-toolkit"
    assert producer.version == "0.2.0"
    assert producer.build is None


def test_invalid_input_fails_before_the_builder_runs(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "build_ui_test_catalog", _no_build)
    output = tmp_path / "ui-test-catalog.json"

    with pytest.raises(InputValidationError) as error:
        normalize_tests([tmp_path / "missing.json"], UI_TESTS, output)

    assert [problem.code for problem in error.value.problems] == [Code.MISSING_INPUT]
    assert error.value.problems[0].location == f"documentation input {str(tmp_path / 'missing.json')!r}"
    assert not output.exists()


def test_two_documentation_inputs_fail_with_multiple_documentation_sources_and_write_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "build_ui_test_catalog", _no_build)
    output = tmp_path / "ui-test-catalog.json"

    with pytest.raises(InputValidationError) as error:
        normalize_tests([DOC_SOURCE, DOC_SOURCE], UI_TESTS, output)

    assert {problem.code for problem in error.value.problems} == {Code.MULTIPLE_DOCUMENTATION_SOURCES}
    assert not output.exists()


def test_one_documentation_path_instead_of_a_sequence_is_a_type_error(tmp_path):
    with pytest.raises(TypeError, match="^normalize-tests - doc_inputs is one path"):
        normalize_tests(str(DOC_SOURCE), UI_TESTS, tmp_path / "ui-test-catalog.json")


@pytest.mark.parametrize("role", ["documentation", "tests"])
def test_a_validation_that_returns_no_input_for_a_role_stops_before_any_transform(
    monkeypatch, tmp_path, documentation, role
):
    # A defect in the shared input validation, which returns an input for every role the command takes.
    validated = ValidatedInputs() if role == "documentation" else ValidatedInputs(documentation=documentation)
    monkeypatch.setattr(service, "validate_inputs", lambda *_args: validated)
    monkeypatch.setattr(service, "build_ui_test_catalog", _no_build)
    output = tmp_path / "ui-test-catalog.json"

    with pytest.raises(RuntimeError, match=f"^normalize-tests - the shared input validation returned no {role} input"):
        normalize_tests([DOC_SOURCE], UI_TESTS, output)

    assert not output.exists()


def test_the_ci_run_is_recorded_and_each_input_run_stays_its_own(ui_tests, tmp_path, monkeypatch):
    input_run = Run(run_id="101", run_attempt="1", actor="collector", workflow="collect", ref="refs/tags/v1")
    collected = ui_tests.model_copy(update={"metadata": ui_tests.metadata.model_copy(update={"run": input_run})})
    input_path = tmp_path / "collected-ui-tests.json"
    output_path = tmp_path / "ui-test-catalog.json"
    write_artifact(collected, input_path)
    monkeypatch.setenv("GITHUB_RUN_ID", "4242")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setenv("GITHUB_ACTOR", "octocat")
    monkeypatch.setenv("GITHUB_WORKFLOW", "docs")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/master")
    monkeypatch.setenv("GITHUB_SHA", "3f2c1ab")

    result = normalize_tests([DOC_SOURCE], input_path, output_path)

    assert result.metadata.run == Run(
        run_id="4242", run_attempt="2", actor="octocat", workflow="docs", ref="refs/heads/master", sha="3f2c1ab"
    )
    assert result.metadata.source_inputs[1].run == input_run


def test_every_input_warning_is_forwarded_unchanged_but_for_its_context(ui_tests, tmp_path, run_command):
    warning = ContractWarning(
        code="UNRESOLVED_RELATION",
        message="A related entity was not found.",
        context="entity_id='US-001' target='FEAT-999'",
        entity_id="US-001",
    )
    input_path = tmp_path / "warned-ui-tests.json"
    write_artifact(ui_tests.model_copy(update={"warnings": [warning]}), input_path)

    result = run_command(DOC_SOURCE, input_path)

    # The documentation fixture's two warnings come first.
    assert len(result.warnings) == 3
    assert result.warnings[2].model_dump(exclude={"context"}) == warning.model_dump(exclude={"context"})
    assert result.warnings[2].context == ("source_input='ui-tests-v1.0.0' entity_id='US-001' target='FEAT-999'")


def test_the_utilities_full_samples_pass_validation_and_lineage(sample_pair, run_command):
    # The command raises FIELD_LOSS on a loss, and writes no file.
    doc_path, tests_path = sample_pair
    result = run_command(doc_path, tests_path)
    written_sample = read_artifact(tests_path, expected="ui-tests")

    assert (
        result.metadata.source_inputs[1].selected_stats.field_occupancy == written_sample.metadata.stats.field_occupancy
    )
    assert [feature_file.feature_file for feature_file in result.feature_files] == [
        "checkout.feature",
        "checkout.feature#12",
    ]
    assert [(group.entity_id, len(group.scenarios)) for group in result.feature_files[0].linked_to_user_story] == [
        ("US-001", 1)
    ]
    assert [(group.entity_id, len(group.scenarios)) for group in result.feature_files[1].linked_to_user_story] == [
        ("US-002", 1)
    ]
    assert not result.feature_files[0].unlinked


def test_over_the_full_samples_every_scenario_path_and_the_background_have_data_in_the_output(sample_pair, run_command):
    occupancy = run_command(*sample_pair).metadata.stats.field_occupancy

    group_roots = (USER_STORY_SCENARIO_ROOT, FUNCTIONALITY_SCENARIO_ROOT, UNLINKED_SCENARIO_ROOT)
    paths = (*SCENARIO_PATHS, "acceptance_criteria[].state")
    empty = [path for path in paths if sum(occupancy.get(f"{root}{path}", 0) for root in group_roots) == 0]
    assert empty == []
    assert occupancy["feature_files[].background[]"] > 0


@pytest.mark.parametrize(
    ("links", "group_name"),
    [
        ((AcLink(id="FUNC-001-01", aspect="happy-path"),), "linked_to_functionality"),
        ((), "unlinked"),
    ],
)
def test_functionality_only_and_unlinked_scenarios_do_not_raise_field_loss(ui_tests, tmp_path, links, group_name):
    input_path = _one_scenario_linking(ui_tests, tmp_path, *links)
    output_path = tmp_path / "ui-test-catalog.json"

    result = normalize_tests([DOC_SOURCE], input_path, output_path)

    feature_file = result.feature_files[0]
    if group_name == "unlinked":
        assert [scenario.scenario_id for scenario in feature_file.unlinked] == [ui_tests.scenarios[4].scenario_id]
    else:
        assert len(feature_file.linked_to_functionality[0].scenarios) == 1
    assert output_path.exists()


def test_in_the_release_view_dropping_every_link_raises_no_field_loss(ui_tests, tmp_path):
    # US-001-03 and FUNC-002-01 are `planned` in the fixture documentation.
    input_path = _one_scenario_linking(ui_tests, tmp_path, AcLink(id="US-001-03"), AcLink(id="FUNC-002-01"))
    output_path = tmp_path / "ui-test-catalog.json"

    result = normalize_tests([DOC_SOURCE], input_path, output_path, view="release")

    feature_file = result.feature_files[0]
    assert [group.entity_id for group in feature_file.linked_to_user_story] == ["US-001"]
    assert [group.entity_id for group in feature_file.linked_to_functionality] == ["FUNC-002"]
    assert feature_file.linked_to_user_story[0].scenarios[0].acceptance_criteria == []
    assert output_path.exists()


def test_dropping_a_mapped_scenario_field_fails_without_writing(monkeypatch, tmp_path):
    build = service.build_ui_test_catalog

    def dropping_aspects(*args, **kwargs):
        result = build(*args, **kwargs)
        for feature_file in result.feature_files:
            for group in feature_file.linked_to_functionality:
                for scenario in group.scenarios:
                    for link in scenario.acceptance_criteria:
                        link.aspect = None
        return result

    monkeypatch.setattr(service, "build_ui_test_catalog", dropping_aspects)
    output_path = tmp_path / "ui-test-catalog.json"

    with pytest.raises(ContractError) as error:
        normalize_tests([DOC_SOURCE], UI_TESTS, output_path)

    assert error.value.code is Code.FIELD_LOSS
    assert "scenarios[].acceptance_criteria[].aspect" in error.value.message
    assert not output_path.exists()


def test_dropping_a_files_background_fails_without_writing(monkeypatch, sample_pair, tmp_path):
    build = service.build_ui_test_catalog

    def dropping_backgrounds(*args, **kwargs):
        result = build(*args, **kwargs)
        for feature_file in result.feature_files:
            feature_file.background = []
        return result

    monkeypatch.setattr(service, "build_ui_test_catalog", dropping_backgrounds)
    output_path = tmp_path / "ui-test-catalog.json"

    with pytest.raises(ContractError) as error:
        normalize_tests([sample_pair[0]], sample_pair[1], output_path)

    assert error.value.code is Code.FIELD_LOSS
    assert "'scenarios[].background[]'" in error.value.message
    assert not output_path.exists()


def test_field_loss_leaves_an_existing_output_untouched(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "check_no_field_loss", lambda _result: _raise_field_loss())
    output_path = tmp_path / "ui-test-catalog.json"
    output_path.write_text("previous run", encoding="utf-8")

    with pytest.raises(ContractError):
        normalize_tests([DOC_SOURCE], UI_TESTS, output_path)

    assert output_path.read_text(encoding="utf-8") == "previous run"


def _raise_field_loss() -> None:
    raise ContractError(Code.FIELD_LOSS, "lost")
