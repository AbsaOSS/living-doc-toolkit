# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for typed coverage-matrix construction: entities, rows, links, summaries, view, and envelope contents."""

from datetime import datetime, timezone
from typing import get_type_hints

import pytest
from living_doc_utilities.contracts import doc_source
from living_doc_utilities.contracts.common import AcceptanceCriterion
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult, CoverageSummary, PlannedSummary
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import AuditStats, ContractWarning
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_tests import AcLink, Scenario, UITestsResult

from living_doc_service_coverage_matrix.builder import build_coverage_matrix

GENERATED_AT = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)


def _build(documentation: DocSourceResult, tests: UITestsResult, view: str = "inner") -> CoverageMatrixResult:
    return build_coverage_matrix(documentation, tests, view=view, generated_at=GENERATED_AT)


def _criterion(ac_id: str, state: str, version: str | None = "1.0.0") -> AcceptanceCriterion:
    return AcceptanceCriterion(
        id=ac_id,
        state=state,
        version=version,
        description=f"{ac_id} holds.",
        removal_planned="2.0.0" if state == "deprecated" else None,
    )


def _with_criteria(documentation: DocSourceResult, *criteria: AcceptanceCriterion) -> DocSourceResult:
    """The fixture with one User Story, `US-001`, holding `criteria`, and no Functionality."""
    user_story = documentation.user_stories[0].model_copy(update={"acceptance_criteria": list(criteria)})
    return documentation.model_copy(update={"user_stories": [user_story], "functionalities": []})


def _scenario(tests: UITestsResult, scenario_id: str, *links: tuple[str, str | None]) -> Scenario:
    return tests.scenarios[0].model_copy(
        update={
            "scenario_id": scenario_id,
            "acceptance_criteria": [AcLink(id=identifier, aspect=aspect) for identifier, aspect in links],
        }
    )


def _with_scenarios(tests: UITestsResult, *scenarios: Scenario) -> UITestsResult:
    return tests.model_copy(update={"scenarios": list(scenarios)})


def _rows(result: CoverageMatrixResult) -> dict[str, list[tuple[str, str, str, list[str]]]]:
    return {
        entity.entity_id: [(row.ac_id, row.state, row.status, row.scenario_ids) for row in entity.acceptance_criteria]
        for entity in result.entities
    }


def test_the_builder_is_typed_on_the_contract_models_in_and_out():
    hints = get_type_hints(build_coverage_matrix)

    assert hints["documentation"] is DocSourceResult
    assert hints["tests"] is UITestsResult
    assert hints["return"] is CoverageMatrixResult


def test_the_builder_takes_and_returns_contract_model_instances(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    assert isinstance(documentation, DocSourceResult)
    assert isinstance(ui_tests, UITestsResult)
    assert isinstance(result, CoverageMatrixResult)


def test_every_user_story_then_every_functionality_has_an_entity_in_input_order(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    assert [(entity.entity_id, entity.type, entity.title, entity.state) for entity in result.entities] == [
        ("US-001", "DocumentedUserStory", "US-001 · Customer Login", "active"),
        ("FUNC-001", "DocumentedFunctionality", "FUNC-001 · Login Page - Validate Password Strength", "active"),
        ("FUNC-002", "DocumentedFunctionality", "FUNC-002 · Login Page - Reject Breached Password", "planned"),
    ]


def test_the_fixture_has_a_row_per_counted_criterion_with_the_scenarios_that_link_it(documentation, ui_tests):
    scenario_ids = [scenario.scenario_id for scenario in ui_tests.scenarios]

    result = _build(documentation, ui_tests)

    # US-001-03 is planned and FUNC-002-01 planned too: neither has a row, and FUNC-002 keeps its entity.
    assert _rows(result) == {
        "US-001": [
            ("US-001-01", "active", "covered", [scenario_ids[4]]),
            ("US-001-02", "active", "not_covered", []),
            ("US-001-04", "deprecated", "covered", [scenario_ids[5]]),
        ],
        "FUNC-001": [
            ("FUNC-001-01", "active", "covered", scenario_ids[:3]),
            ("FUNC-001-02", "active", "not_covered", []),
            ("FUNC-001-03", "active", "covered", [scenario_ids[3]]),
        ],
        "FUNC-002": [],
    }


def test_a_row_carries_no_aspect_and_no_keyword_while_coverage_is_per_criterion(documentation, ui_tests):
    # FUNC-001-01 declares three aspects and FUNC-001-03 a keyword; each is one plain row.
    result = _build(documentation, ui_tests)

    rows = [row for entity in result.entities for row in entity.acceptance_criteria]
    assert all(row.aspects == [] and row.keyword is None for row in rows)


def test_every_summary_comes_from_its_rows_and_the_root_from_every_row(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    assert [entity.summary for entity in result.entities] == [
        CoverageSummary(counted_acs=3, covered_acs=2, partially_covered_acs=0, not_covered_acs=1, coverage_pct=66.7),
        CoverageSummary(counted_acs=3, covered_acs=2, partially_covered_acs=0, not_covered_acs=1, coverage_pct=66.7),
        CoverageSummary(counted_acs=0, covered_acs=0, partially_covered_acs=0, not_covered_acs=0, coverage_pct=None),
    ]
    assert result.summary == CoverageSummary(
        counted_acs=6, covered_acs=4, partially_covered_acs=0, not_covered_acs=2, coverage_pct=66.7
    )


def test_the_fixture_planned_summary_counts_one_targeted_and_one_backlog_criterion(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    assert result.planned_summary == PlannedSummary(total=2, backlog=1, by_target_version={"1.1.0": 1})


def test_a_deprecated_row_counts_like_an_active_one(documentation, ui_tests):
    tests = _with_scenarios(ui_tests, _scenario(ui_tests, "SCN-1", ("US-001-02", None)))
    built = _with_criteria(documentation, _criterion("US-001-01", "active"), _criterion("US-001-02", "deprecated"))

    result = _build(built, tests)

    assert _rows(result)["US-001"] == [
        ("US-001-01", "active", "not_covered", []),
        ("US-001-02", "deprecated", "covered", ["SCN-1"]),
    ]
    assert result.summary.counted_acs == 2
    assert result.summary.coverage_pct == 50.0


def test_planned_criteria_count_by_target_version_or_backlog_and_in_review_ones_nowhere(documentation, ui_tests):
    built = _with_criteria(
        documentation,
        _criterion("US-001-01", "planned", "2.0.0"),
        _criterion("US-001-02", "planned", "1.1.0"),
        _criterion("US-001-03", "planned", None),
        _criterion("US-001-04", "in_review", "1.0.0"),
        _criterion("US-001-05", "planned", "2.0.0"),
        _criterion("US-001-06", "active"),
    )

    result = _build(built, ui_tests)

    assert result.planned_summary == PlannedSummary(total=4, backlog=1, by_target_version={"2.0.0": 2, "1.1.0": 1})
    assert list(result.planned_summary.by_target_version) == ["2.0.0", "1.1.0"]
    assert [row.ac_id for row in result.entities[0].acceptance_criteria] == ["US-001-06"]


def test_a_scenario_is_listed_once_per_row_in_input_order(documentation, ui_tests):
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-B", ("US-001-01", "desktop"), ("US-001-01", "mobile")),
        _scenario(ui_tests, "SCN-A", ("US-001-02", None), ("US-001-01", None)),
        _scenario(ui_tests, "SCN-C", ("US-001-01", None)),
    )
    built = _with_criteria(documentation, _criterion("US-001-01", "active"), _criterion("US-001-02", "active"))

    result = _build(built, tests)

    assert _rows(result)["US-001"] == [
        ("US-001-01", "active", "covered", ["SCN-B", "SCN-A", "SCN-C"]),
        ("US-001-02", "active", "covered", ["SCN-A"]),
    ]


def test_a_link_to_a_criterion_without_a_row_counts_nowhere_and_raises_nothing(documentation, ui_tests):
    built = _with_criteria(
        documentation,
        _criterion("US-001-01", "active"),
        _criterion("US-001-02", "planned", None),
        _criterion("US-001-03", "in_review"),
    )
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-1", ("US-001-02", None), ("US-001-03", None), ("US-999-01", None)),
    )

    result = _build(built, tests)

    assert _rows(result)["US-001"] == [("US-001-01", "active", "not_covered", [])]
    assert result.summary.counted_acs == 1
    assert result.summary.coverage_pct == 0.0
    # Only the documentation input's own two warnings, forwarded; the links add none.
    assert len(result.warnings) == len(documentation.warnings) == 2


def test_links_match_by_criterion_id_whatever_repository_the_scenario_is_in(documentation, ui_tests):
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "org/repo-a/login.feature/sign-in", ("US-001-01", None)),
        _scenario(ui_tests, "org/repo-b/login.feature/sign-in", ("US-001-01", None)),
    )
    built = _with_criteria(documentation, _criterion("US-001-01", "active"))

    result = _build(built, tests)

    assert result.entities[0].acceptance_criteria[0].scenario_ids == [
        "org/repo-a/login.feature/sign-in",
        "org/repo-b/login.feature/sign-in",
    ]


def test_the_view_sets_document_view_and_changes_no_row_or_count(documentation, ui_tests):
    inner = _build(documentation, ui_tests, "inner")
    release = _build(documentation, ui_tests, "release")

    assert inner.document.view == "inner"
    assert release.document.view == "release"
    assert release.model_dump(exclude={"document"}) == inner.model_dump(exclude={"document"})


def test_the_source_is_the_documentation_inputs_with_each_tests_system_added_once(documentation, ui_tests):
    tests_source = ui_tests.metadata.source.model_copy(update={"systems": ["AzureDevOps", "GitHub", "AzureDevOps"]})
    tests = ui_tests.model_copy(update={"metadata": ui_tests.metadata.model_copy(update={"source": tests_source})})

    result = _build(documentation, tests)

    assert result.metadata.source == documentation.metadata.source.model_copy(
        update={"systems": ["GitHub", "AzureDevOps"]}
    )
    assert documentation.metadata.source.systems == ["GitHub"]


def test_the_source_inputs_are_the_documentation_entry_then_the_tests_entry(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    entries = result.metadata.source_inputs
    assert [entry.schema_version for entry in entries] == ["doc-source-v1.0.0", "ui-tests-v1.0.0"]
    for entry, given in zip(entries, (documentation, ui_tests)):
        assert entry.producer == given.metadata.producer
        assert entry.run == given.metadata.run
        assert entry.source == given.metadata.source
        assert entry.stats == AuditStats.model_validate(given.metadata.stats.model_dump())
    assert entries[1].selected_stats == entries[1].stats


def test_the_documentation_selected_stats_cover_the_counted_criteria_of_user_stories_and_functionalities(
    documentation, ui_tests
):
    result = _build(documentation, ui_tests)

    selected = result.metadata.source_inputs[0].selected_stats
    stats = result.metadata.source_inputs[0].stats
    counted = documentation.model_copy(
        update={
            "user_stories": [
                documentation.user_stories[0].model_copy(
                    update={
                        "acceptance_criteria": [documentation.user_stories[0].acceptance_criteria[i] for i in (0, 1, 3)]
                    }
                )
            ],
            "features": [],
            "functionalities": [
                documentation.functionalities[0],
                documentation.functionalities[1].model_copy(update={"acceptance_criteria": []}),
            ],
        }
    )
    expected = compute_stats(counted, doc_source.RECORD_ROOTS, documentation.metadata.stats.cardinality)
    assert selected == AuditStats.model_validate(expected.model_dump())
    assert (selected.cardinality.entities, selected.cardinality.acceptance_criteria) == (3, 6)
    assert (stats.cardinality.entities, stats.cardinality.acceptance_criteria) == (5, 8)
    assert selected.field_occupancy["features[].entity_id"] == 0
    assert selected.field_occupancy["user_stories[].acceptance_criteria[].id"] == 3
    assert selected.field_occupancy["functionalities[].acceptance_criteria[].id"] == 3


def test_every_warning_is_forwarded_documentation_first_each_naming_its_own_input(documentation, ui_tests):
    tests_warning = ContractWarning(code="STALE_AC_REF", message="An unknown criterion.", context="tag='@AC:US-9-1'")
    tests = ui_tests.model_copy(update={"warnings": [tests_warning]})

    result = _build(documentation, tests)

    assert [(warning.code, warning.context) for warning in result.warnings] == [
        ("FEATURE_WITHOUT_FUNCTIONALITY", "source_input='doc-source-v1.0.0' entity_id='FEAT-003'"),
        ("UNRESOLVED_RELATION", "source_input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'"),
        ("STALE_AC_REF", "source_input='ui-tests-v1.0.0' tag='@AC:US-9-1'"),
    ]
    assert result.warnings[2].model_dump(exclude={"context"}) == tests_warning.model_dump(exclude={"context"})


def test_the_producer_is_the_toolkit_and_the_caller_counts_are_zero(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    producer = result.metadata.producer
    assert (producer.name, producer.version, producer.build) == ("AbsaOSS/living-doc-toolkit", "0.1.0", None)
    cardinality = result.metadata.stats.cardinality
    counts = (
        cardinality.sources_configured,
        cardinality.sources_failed,
        cardinality.unresolved_refs,
        cardinality.entities_skipped,
    )
    assert counts == (0, 0, 0, 0)
    assert result.metadata.generated_at == GENERATED_AT


def test_a_feature_in_a_counted_list_is_refused(documentation, ui_tests):
    # A `doc-source` model holds Features in `features[]` only; `model_copy` skips that check.
    feature = documentation.features[0]
    built = documentation.model_copy(update={"user_stories": [feature]})

    with pytest.raises(ValueError, match="^entity 'FEAT-001' is a Feature"):
        _build(built, ui_tests)
