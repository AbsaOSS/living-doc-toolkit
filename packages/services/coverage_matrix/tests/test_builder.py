# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for typed coverage-matrix construction: entities, rows and their aspects, links, the link warnings,
summaries, view, and envelope contents.
"""

from datetime import datetime, timezone
from typing import get_type_hints

import pytest
from living_doc_utilities.contracts import doc_source
from living_doc_utilities.contracts.common import AcceptanceCriterion
from living_doc_utilities.contracts.coverage_matrix import (
    AcCoverage,
    AspectCoverage,
    CoverageMatrixResult,
    CoverageSummary,
    PlannedSummary,
)
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import AuditStats, ContractWarning
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_tests import AcLink, Scenario, UITestsResult

from living_doc_service_coverage_matrix.builder import build_coverage_matrix

GENERATED_AT = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)
DEVICES = ("desktop", "mobile", "tablet")


def _build(documentation: DocSourceResult, tests: UITestsResult, view: str = "inner") -> CoverageMatrixResult:
    return build_coverage_matrix(documentation, tests, view=view, generated_at=GENERATED_AT)


def _criterion(
    ac_id: str,
    state: str,
    version: str | None = "1.0.0",
    *,
    aspects: tuple[str, ...] = (),
    keyword: str | None = None,
) -> AcceptanceCriterion:
    """A criterion; with `keyword`, its `aspects` are that keyword's values, as the grammar stores them."""
    return AcceptanceCriterion(
        id=ac_id,
        state=state,
        version=version,
        description=f"{ac_id} holds.",
        aspect=list(aspects),
        removal_planned="2.0.0" if state == "deprecated" else None,
        placeholder_values={keyword: list(aspects)} if keyword else {},
    )


def _aspect(aspect: str, *scenario_ids: str) -> AspectCoverage:
    return AspectCoverage(
        aspect=aspect, status="covered" if scenario_ids else "not_covered", scenario_ids=list(scenario_ids)
    )


def _row(result: CoverageMatrixResult, ac_id: str) -> AcCoverage:
    return next(row for entity in result.entities for row in entity.acceptance_criteria if row.ac_id == ac_id)


def _own_warnings(result: CoverageMatrixResult, documentation: DocSourceResult) -> list[ContractWarning]:
    """The warnings the builder raises itself: those after the documentation input's, forwarded."""
    return result.warnings[len(documentation.warnings) :]


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

    # US-001-03 is planned and FUNC-002-01 planned too: neither has a row, and FUNC-002 keeps its entity. A row with
    # aspects lists its scenarios under them, and its own scenario_ids stays empty.
    assert _rows(result) == {
        "US-001": [
            ("US-001-01", "active", "covered", [scenario_ids[4]]),
            ("US-001-02", "active", "not_covered", []),
            ("US-001-04", "deprecated", "covered", [scenario_ids[5]]),
        ],
        "FUNC-001": [
            ("FUNC-001-01", "active", "covered", []),
            ("FUNC-001-02", "active", "not_covered", []),
            ("FUNC-001-03", "active", "partially_covered", []),
        ],
        "FUNC-002": [],
    }


def test_the_fixture_criteria_with_aspects_are_counted_per_aspect_and_the_keyword_one_names_its_keyword(
    documentation, ui_tests
):
    scenario_ids = [scenario.scenario_id for scenario in ui_tests.scenarios]

    result = _build(documentation, ui_tests)

    every_aspect, plain, keyword = result.entities[1].acceptance_criteria
    assert (every_aspect.keyword, every_aspect.aspects) == (
        None,
        [
            _aspect("minimum-length", scenario_ids[0]),
            _aspect("character-classes", scenario_ids[1]),
            _aspect("no-username", scenario_ids[2]),
        ],
    )
    assert (plain.keyword, plain.aspects) == (None, [])
    assert (keyword.keyword, keyword.aspects) == (
        "rule",
        [_aspect("minimum-length", scenario_ids[3]), _aspect("character-classes"), _aspect("no-username")],
    )
    assert (keyword.covered_aspects(), len(keyword.aspects)) == (1, 3)
    # US-001's criteria declare no aspects: each row stays plain.
    assert all(row.aspects == [] and row.keyword is None for row in result.entities[0].acceptance_criteria)


def test_every_summary_comes_from_its_rows_and_the_root_from_every_row(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    # FUNC-001: 1 + 0 + 1/3 over three rows.
    assert [entity.summary for entity in result.entities] == [
        CoverageSummary(counted_acs=3, covered_acs=2, partially_covered_acs=0, not_covered_acs=1, coverage_pct=66.7),
        CoverageSummary(counted_acs=3, covered_acs=1, partially_covered_acs=1, not_covered_acs=1, coverage_pct=44.4),
        CoverageSummary(counted_acs=0, covered_acs=0, partially_covered_acs=0, not_covered_acs=0, coverage_pct=None),
    ]
    assert result.summary == CoverageSummary(
        counted_acs=6, covered_acs=3, partially_covered_acs=1, not_covered_acs=2, coverage_pct=55.6
    )


def test_a_criterion_with_every_aspect_linked_is_covered_and_keeps_its_own_scenario_ids_empty(documentation, ui_tests):
    built = _with_criteria(documentation, _criterion("US-001-01", "active", aspects=DEVICES))
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-1", ("US-001-01", "desktop")),
        _scenario(ui_tests, "SCN-2", ("US-001-01", "mobile"), ("US-001-01", "tablet")),
    )

    row = _row(_build(built, tests), "US-001-01")

    assert (row.status, row.scenario_ids, row.keyword) == ("covered", [], None)
    assert row.aspects == [_aspect("desktop", "SCN-1"), _aspect("mobile", "SCN-2"), _aspect("tablet", "SCN-2")]


def test_a_criterion_with_some_aspects_linked_is_partially_covered_and_weighs_its_covered_aspects(
    documentation, ui_tests
):
    built = _with_criteria(documentation, _criterion("US-001-01", "active", aspects=DEVICES))
    tests = _with_scenarios(ui_tests, _scenario(ui_tests, "SCN-1", ("US-001-01", "mobile")))

    result = _build(built, tests)

    row = _row(result, "US-001-01")
    assert (row.status, row.scenario_ids) == ("partially_covered", [])
    assert row.aspects == [_aspect("desktop"), _aspect("mobile", "SCN-1"), _aspect("tablet")]
    assert (row.covered_aspects(), len(row.aspects)) == (1, 3)
    assert result.summary == CoverageSummary(
        counted_acs=1, covered_acs=0, partially_covered_acs=1, not_covered_acs=0, coverage_pct=33.3
    )


def test_a_criterion_with_aspects_and_no_scenario_is_not_covered_on_every_aspect(documentation, ui_tests):
    built = _with_criteria(documentation, _criterion("US-001-01", "active", aspects=DEVICES))

    row = _row(_build(built, _with_scenarios(ui_tests)), "US-001-01")

    assert (row.status, row.scenario_ids) == ("not_covered", [])
    assert row.aspects == [_aspect(aspect) for aspect in DEVICES]


def test_a_bare_link_lists_its_scenario_under_every_declared_aspect(documentation, ui_tests):
    built = _with_criteria(documentation, _criterion("US-001-01", "active", aspects=DEVICES))
    tests = _with_scenarios(ui_tests, _scenario(ui_tests, "SCN-1", ("US-001-01", None)))

    row = _row(_build(built, tests), "US-001-01")

    assert row.status == "covered"
    assert row.aspects == [_aspect(aspect, "SCN-1") for aspect in DEVICES]


def test_each_aspect_lists_a_scenario_once_in_input_order(documentation, ui_tests):
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-B", ("US-001-01", "desktop"), ("US-001-01", "mobile"), ("US-001-01", "desktop")),
        _scenario(ui_tests, "SCN-A", ("US-001-01", "mobile"), ("US-001-01", None)),
    )
    built = _with_criteria(documentation, _criterion("US-001-01", "active", aspects=DEVICES))

    row = _row(_build(built, tests), "US-001-01")

    assert row.aspects == [
        _aspect("desktop", "SCN-B", "SCN-A"),
        _aspect("mobile", "SCN-B", "SCN-A"),
        _aspect("tablet", "SCN-A"),
    ]


def test_a_keyword_criterion_is_counted_exactly_as_an_aspect_one_and_names_its_keyword(documentation, ui_tests):
    built = _with_criteria(
        documentation,
        _criterion("US-001-01", "active", aspects=DEVICES),
        _criterion("US-001-02", "active", aspects=DEVICES, keyword="payment_field"),
        _criterion("US-001-03", "active"),
    )
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-1", ("US-001-01", "desktop"), ("US-001-02", "desktop"), ("US-001-03", None)),
    )

    aspect_row, keyword_row, plain_row = _build(built, tests).entities[0].acceptance_criteria

    assert keyword_row.model_dump(exclude={"ac_id", "keyword"}) == aspect_row.model_dump(exclude={"ac_id", "keyword"})
    assert keyword_row.status == "partially_covered"
    # The keyword is the criterion's one placeholder_values key, as stored; an Aspect: row and a plain row have none.
    assert (aspect_row.keyword, keyword_row.keyword, plain_row.keyword) == (None, "payment_field", None)
    assert (plain_row.aspects, plain_row.scenario_ids) == ([], ["SCN-1"])


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


def test_a_link_to_an_unknown_criterion_is_a_stale_reference_and_counts_nowhere(documentation, ui_tests):
    built = _with_criteria(documentation, _criterion("US-001-01", "active"))
    tests = _with_scenarios(
        ui_tests, _scenario(ui_tests, "SCN-1", ("US-001-99", None), ("FUNC-404-01", "desktop"), ("US-001-99", None))
    )

    result = _build(built, tests)

    assert _rows(result)["US-001"] == [("US-001-01", "active", "not_covered", [])]
    # One warning per scenario and criterion; line_no, path and source_url are a collector's to fill.
    assert _own_warnings(result, built) == [
        ContractWarning(
            code="STALE_AC_REF",
            message="Scenario 'SCN-1' links acceptance criterion 'US-001-99', which no User Story or Functionality in "
            "the documentation has: the link counts nowhere. Fix the tag, or document the criterion.",
            context="scenario_id='SCN-1'",
            entity_id="US-001",
            ac_id="US-001-99",
        ),
        ContractWarning(
            code="STALE_AC_REF",
            message="Scenario 'SCN-1' links acceptance criterion 'FUNC-404-01', which no User Story or Functionality "
            "in the documentation has: the link counts nowhere. Fix the tag, or document the criterion.",
            context="scenario_id='SCN-1'",
            entity_id="FUNC-404",
            ac_id="FUNC-404-01",
        ),
    ]


def test_a_link_to_an_aspect_its_criterion_does_not_declare_is_a_stale_reference_and_counts_nowhere(
    documentation, ui_tests
):
    tests = _with_scenarios(
        ui_tests,
        _scenario(
            ui_tests,
            "SCN-1",
            ("FUNC-001-01", "no-such-rule"),
            ("FUNC-001-01", "no-such-rule"),
            ("FUNC-001-01", "minimum-length"),
            ("FUNC-001-01", "Minimum-Length"),
        ),
    )

    result = _build(documentation, tests)

    assert _row(result, "FUNC-001-01").aspects == [
        _aspect("minimum-length", "SCN-1"),
        _aspect("character-classes"),
        _aspect("no-username"),
    ]
    # One warning per scenario, criterion and aspect; an aspect is matched as written.
    assert _own_warnings(result, documentation) == [
        ContractWarning(
            code="STALE_AC_REF",
            message=f"Scenario 'SCN-1' links aspect {aspect!r} of acceptance criterion 'FUNC-001-01', which the "
            "criterion does not declare: the link counts nowhere. Fix the tag, or declare the aspect.",
            context=f"scenario_id='SCN-1' aspect={aspect!r}",
            entity_id="FUNC-001",
            ac_id="FUNC-001-01",
        )
        for aspect in ("no-such-rule", "Minimum-Length")
    ]


def test_a_link_with_an_aspect_to_a_criterion_without_aspects_covers_it_and_is_a_stale_reference(
    documentation, ui_tests
):
    # US-001-02 declares no aspects and no scenario links it in the fixture.
    tests = _with_scenarios(ui_tests, *ui_tests.scenarios, _scenario(ui_tests, "SCN-1", ("US-001-02", "desktop")))

    result = _build(documentation, tests)

    row = _row(result, "US-001-02")
    assert (row.status, row.scenario_ids, row.aspects) == ("covered", ["SCN-1"], [])
    assert _own_warnings(result, documentation) == [
        ContractWarning(
            code="STALE_AC_REF",
            message="Scenario 'SCN-1' links aspect 'desktop' of acceptance criterion 'US-001-02', which declares no "
            "aspects: the link covers the whole criterion, as a bare one does. Drop the aspect from the tag, or "
            "declare the criterion's aspects.",
            context="scenario_id='SCN-1' aspect='desktop'",
            entity_id="US-001",
            ac_id="US-001-02",
        )
    ]


def test_a_link_to_a_planned_criterion_warns_and_the_criterion_has_no_row(documentation, ui_tests):
    # US-001-03 is planned in the fixture; the warning is the same whatever the link's aspect.
    tests = _with_scenarios(
        ui_tests,
        *ui_tests.scenarios,
        _scenario(ui_tests, "SCN-1", ("US-001-03", None), ("US-001-03", "no-such-aspect")),
    )

    result = _build(documentation, tests)

    assert "US-001-03" not in [row.ac_id for row in result.entities[0].acceptance_criteria]
    assert result.summary == _build(documentation, ui_tests).summary
    assert _own_warnings(result, documentation) == [
        ContractWarning(
            code="PLANNED_AC_HAS_TESTS",
            message="Scenario 'SCN-1' links acceptance criterion 'US-001-03', which is planned: the matrix counts no "
            "planned criterion, so the link counts nowhere until the criterion is active.",
            context="scenario_id='SCN-1'",
            entity_id="US-001",
            ac_id="US-001-03",
        )
    ]


def test_a_link_to_an_in_review_criterion_warns_and_the_criterion_has_no_row(documentation, ui_tests):
    built = _with_criteria(
        documentation, _criterion("US-001-01", "active"), _criterion("US-001-02", "in_review", aspects=DEVICES)
    )
    tests = _with_scenarios(ui_tests, _scenario(ui_tests, "SCN-1", ("US-001-02", "desktop"), ("US-001-02", None)))

    result = _build(built, tests)

    assert _rows(result)["US-001"] == [("US-001-01", "active", "not_covered", [])]
    assert _own_warnings(result, built) == [
        ContractWarning(
            code="IN_REVIEW_AC_HAS_TESTS",
            message="Scenario 'SCN-1' links acceptance criterion 'US-001-02', which is in review: the matrix counts "
            "no criterion in review, so the link counts nowhere. If its work has merged, set the criterion active.",
            context="scenario_id='SCN-1'",
            entity_id="US-001",
            ac_id="US-001-02",
        )
    ]


def test_the_link_warnings_follow_the_forwarded_ones_in_scenario_then_link_order(documentation, ui_tests):
    tests_warning = ContractWarning(code="STALE_AC_REF", message="An unknown criterion.", context="tag='@AC:US-9-1'")
    built = _with_criteria(
        documentation,
        _criterion("US-001-01", "active", aspects=DEVICES),
        _criterion("US-001-02", "planned", None),
        _criterion("US-001-03", "in_review"),
    )
    tests = _with_scenarios(
        ui_tests,
        _scenario(ui_tests, "SCN-B", ("US-001-03", None), ("US-001-01", "watch"), ("US-001-02", None)),
        _scenario(ui_tests, "SCN-A", ("US-001-99", None), ("US-001-03", None)),
    ).model_copy(update={"warnings": [tests_warning]})

    result = _build(built, tests)

    assert [(warning.code, warning.ac_id, warning.context) for warning in result.warnings] == [
        ("FEATURE_WITHOUT_FUNCTIONALITY", None, "source_input='doc-source-v1.0.0' entity_id='FEAT-003'"),
        ("UNRESOLVED_RELATION", None, "source_input='doc-source-v1.0.0' entity_id='FEAT-003' target='FEAT-002'"),
        ("STALE_AC_REF", None, "source_input='ui-tests-v1.0.0' tag='@AC:US-9-1'"),
        ("IN_REVIEW_AC_HAS_TESTS", "US-001-03", "scenario_id='SCN-B'"),
        ("STALE_AC_REF", "US-001-01", "scenario_id='SCN-B' aspect='watch'"),
        ("PLANNED_AC_HAS_TESTS", "US-001-02", "scenario_id='SCN-B'"),
        ("STALE_AC_REF", "US-001-99", "scenario_id='SCN-A'"),
        ("IN_REVIEW_AC_HAS_TESTS", "US-001-03", "scenario_id='SCN-A'"),
    ]


def test_the_fixture_pair_raises_no_link_warning(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    assert _own_warnings(result, documentation) == []


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
