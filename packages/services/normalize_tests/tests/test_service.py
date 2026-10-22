# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the `normalize-tests` command and its run-time field-loss check."""

import json
from pathlib import Path

import pytest
from living_doc_core.input_validation import InputValidationError
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import AuditStats, ContractWarning, Run
from living_doc_utilities.contracts.io import read_artifact, write_artifact
from living_doc_utilities.contracts.testing import full_sample
from living_doc_utilities.contracts.ui_tests import AcLink

from living_doc_service_normalize_tests import service
from living_doc_service_normalize_tests.builder import build_ui_test_catalog
from living_doc_service_normalize_tests.lineage import FUNCTIONALITY_SCENARIO_ROOT, USER_STORY_SCENARIO_ROOT
from living_doc_service_normalize_tests.service import normalize_tests

FIXTURE = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "collector-gh" / "ui-tests.json"
EXPECTED = Path(__file__).resolve().parent / "expected"


def _masked(payload: dict) -> dict:
    payload["metadata"]["generated_at"] = "<masked>"
    return payload


def _written(path: Path) -> dict:
    return _masked(json.loads(path.read_text(encoding="utf-8")))


def test_the_command_writes_the_committed_fixture_golden(tmp_path):
    output = tmp_path / "ui-test-catalog.json"

    normalize_tests(FIXTURE, output)

    assert _written(output) == _written(EXPECTED / "ui-test-catalog.json")


def test_the_fixture_catalog_has_two_files_and_aggregates_functionality_fields(ui_tests, tmp_path):
    output = tmp_path / "ui-test-catalog.json"
    normalize_tests(FIXTURE, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    result = build_ui_test_catalog(ui_tests, generated_at=ui_tests.metadata.generated_at)

    assert result.document.view == "inner"
    assert len(result.feature_files) == 2
    assert result.feature_files[0].linked_to_functionality[0].entity_id == "FUNC-001"
    assert len(result.feature_files[0].linked_to_functionality[0].scenarios) == 4
    assert result.feature_files[1].linked_to_user_story[0].entity_id == "US-001"
    assert len(result.feature_files[1].linked_to_user_story[0].scenarios) == 2
    assert not any(feature_file.unlinked for feature_file in result.feature_files)
    assert (
        payload["metadata"]["stats"]["field_occupancy"][f"{USER_STORY_SCENARIO_ROOT}acceptance_criteria[].aspect"] == 0
    )
    assert (
        payload["metadata"]["stats"]["field_occupancy"][f"{FUNCTIONALITY_SCENARIO_ROOT}acceptance_criteria[].aspect"]
        == 4
    )


def test_the_command_copies_source_and_input_audit_stats(ui_tests, run_command):
    result = run_command(FIXTURE)
    entry = result.metadata.source_inputs[0]

    assert result.metadata.source == ui_tests.metadata.source
    assert result.document.view == "inner"
    assert len(result.metadata.source_inputs) == 1
    assert entry.schema_version == ui_tests.schema_version
    assert entry.producer == ui_tests.metadata.producer
    assert entry.run == ui_tests.metadata.run
    assert entry.source == ui_tests.metadata.source
    assert entry.stats == AuditStats.model_validate(ui_tests.metadata.stats.model_dump())
    assert entry.selected_stats == entry.stats
    assert result.metadata.stats.cardinality.sources_configured == 0
    assert result.metadata.stats.cardinality.sources_failed == 0
    assert result.metadata.stats.cardinality.unresolved_refs == 0
    assert result.metadata.stats.cardinality.entities_skipped == 0


def test_the_producer_uses_the_toolkit_identity_and_keeps_build_null(ui_tests, run_command):
    producer = run_command(FIXTURE).metadata.producer

    assert producer.name == "AbsaOSS/living-doc-toolkit"
    assert producer.version == "0.1.0"
    assert producer.build is None


def test_invalid_input_fails_before_the_builder_runs(monkeypatch, tmp_path):
    def no_build(*_args, **_kwargs):
        raise AssertionError("the builder ran")

    monkeypatch.setattr(service, "build_ui_test_catalog", no_build)
    output = tmp_path / "ui-test-catalog.json"

    with pytest.raises(InputValidationError) as error:
        normalize_tests(tmp_path / "missing.json", output)

    assert [problem.code for problem in error.value.problems] == [Code.MISSING_INPUT]
    assert not output.exists()


def test_the_ci_run_is_recorded_and_the_input_run_stays_its_own(ui_tests, tmp_path, monkeypatch):
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

    result = normalize_tests(input_path, output_path)

    assert result.metadata.run == Run(
        run_id="4242", run_attempt="2", actor="octocat", workflow="docs", ref="refs/heads/master", sha="3f2c1ab"
    )
    assert result.metadata.source_inputs[0].run == input_run


def test_every_input_warning_is_forwarded_unchanged_but_for_its_context(ui_tests, tmp_path, run_command):
    warning = ContractWarning(
        code="UNRESOLVED_RELATION",
        message="A related entity was not found.",
        context="entity_id='US-001' target='FEAT-999'",
        entity_id="US-001",
    )
    input_path = tmp_path / "warned-ui-tests.json"
    write_artifact(ui_tests.model_copy(update={"warnings": [warning]}), input_path)

    result = run_command(input_path)

    assert len(result.warnings) == 1
    assert result.warnings[0].model_dump(exclude={"context"}) == warning.model_dump(exclude={"context"})
    assert result.warnings[0].context == ("source_input='ui-tests-v1.0.0' entity_id='US-001' target='FEAT-999'")


def test_the_utilities_full_sample_passes_validation_and_lineage(ui_tests, tmp_path):
    sample = full_sample("ui-tests-v1.0.0")
    input_path = tmp_path / "full-sample.json"
    output_path = tmp_path / "ui-test-catalog.json"
    write_artifact(sample, input_path)

    result = normalize_tests(input_path, output_path)
    written_sample = read_artifact(input_path, expected="ui-tests")

    assert (
        result.metadata.source_inputs[0].selected_stats.field_occupancy == written_sample.metadata.stats.field_occupancy
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
    assert output_path.exists()


@pytest.mark.parametrize(
    ("links", "group_name"),
    [
        ((AcLink(id="FUNC-001-01", aspect="happy-path"),), "linked_to_functionality"),
        ((), "unlinked"),
    ],
)
def test_functionality_only_and_unlinked_scenarios_do_not_raise_field_loss(ui_tests, tmp_path, links, group_name):
    scenario = ui_tests.scenarios[0].model_copy(update={"acceptance_criteria": list(links)})
    tests = ui_tests.model_copy(update={"scenarios": [scenario]})
    input_path = tmp_path / "ui-tests.json"
    output_path = tmp_path / "ui-test-catalog.json"
    write_artifact(tests, input_path)

    result = normalize_tests(input_path, output_path)

    feature_file = result.feature_files[0]
    if group_name == "unlinked":
        assert feature_file.unlinked == [scenario]
    else:
        assert len(feature_file.linked_to_functionality[0].scenarios) == 1
    assert output_path.exists()


def test_dropping_a_mapped_scenario_field_fails_without_writing(monkeypatch, tmp_path):
    build = service.build_ui_test_catalog

    def dropping_aspects(*args, **kwargs):
        result = build(*args, **kwargs)
        result.feature_files = [
            feature_file.model_copy(
                update={
                    "linked_to_functionality": [
                        group.model_copy(
                            update={
                                "scenarios": [
                                    scenario.model_copy(
                                        update={
                                            "acceptance_criteria": [
                                                link.model_copy(update={"aspect": None})
                                                for link in scenario.acceptance_criteria
                                            ]
                                        }
                                    )
                                    for scenario in group.scenarios
                                ]
                            }
                        )
                        for group in feature_file.linked_to_functionality
                    ]
                }
            )
            for feature_file in result.feature_files
        ]
        return result

    monkeypatch.setattr(service, "build_ui_test_catalog", dropping_aspects)
    output_path = tmp_path / "ui-test-catalog.json"

    with pytest.raises(ContractError) as error:
        normalize_tests(FIXTURE, output_path)

    assert error.value.code is Code.FIELD_LOSS
    assert "scenarios[].acceptance_criteria[].aspect" in error.value.message
    assert not output_path.exists()


def test_field_loss_leaves_an_existing_output_untouched(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "check_no_field_loss", lambda _result: _raise_field_loss())
    output_path = tmp_path / "ui-test-catalog.json"
    output_path.write_text("previous run", encoding="utf-8")

    with pytest.raises(ContractError):
        normalize_tests(FIXTURE, output_path)

    assert output_path.read_text(encoding="utf-8") == "previous run"


def _raise_field_loss() -> None:
    raise ContractError(Code.FIELD_LOSS, "lost")
