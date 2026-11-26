# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for typed catalog construction: grouping and order, link states, the release view, and the envelope."""

from datetime import datetime, timezone
from typing import get_type_hints

import pytest
from living_doc_utilities.contracts import doc_source as doc_source_contract
from living_doc_utilities.contracts import ui_tests as ui_tests_contract
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import AuditStats, ContractWarning
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_test_catalog import CatalogScenario, UiTestCatalogResult
from living_doc_utilities.contracts.ui_tests import AcLink, Scenario, UITestsResult

from living_doc_service_normalize_tests.builder import build_ui_test_catalog

GENERATED_AT = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def _scenario(
    tests: UITestsResult,
    scenario_id: str,
    native_id: str,
    links: tuple[tuple[str, str | None], ...] = (),
    **fields: object,
) -> Scenario:
    template = tests.scenarios[0]
    return template.model_copy(
        update={
            "scenario_id": scenario_id,
            "source_ref": template.source_ref.model_copy(update={"native_id": native_id}),
            "acceptance_criteria": [AcLink(id=identifier, aspect=aspect) for identifier, aspect in links],
            **fields,
        }
    )


def _build(documentation: DocSourceResult, tests: UITestsResult, view="inner") -> UiTestCatalogResult:
    return build_ui_test_catalog(documentation, tests, view=view, generated_at=GENERATED_AT)


def _carried(scenario: Scenario) -> dict:
    """What the catalog carries of a scenario unchanged: every field but its file's background and its links' states."""
    return scenario.model_dump(exclude={"background"})


def _without_states(scenario: CatalogScenario) -> dict:
    payload = scenario.model_dump()
    for link in payload["acceptance_criteria"]:
        del link["state"]
    return payload


def _links(scenario: CatalogScenario) -> list[tuple[str, str | None, str | None]]:
    return [(link.id, link.aspect, link.state) for link in scenario.acceptance_criteria]


def _with_in_review(documentation: DocSourceResult, criterion_id: str) -> DocSourceResult:
    """The documentation with one User Story criterion `in_review`."""
    stories = [
        story.model_copy(
            update={
                "acceptance_criteria": [
                    criterion.model_copy(update={"state": "in_review"}) if criterion.id == criterion_id else criterion
                    for criterion in story.acceptance_criteria
                ]
            }
        )
        for story in documentation.user_stories
    ]
    return documentation.model_copy(update={"user_stories": stories})


def test_the_builder_is_typed_on_the_contract_models_in_and_out():
    hints = get_type_hints(build_ui_test_catalog)

    assert hints["documentation"] is DocSourceResult
    assert hints["tests"] is UITestsResult
    assert hints["return"] is UiTestCatalogResult


def test_the_fixture_groups_feature_files_and_entities_in_input_order(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    functionality_file, user_story_file = result.feature_files
    assert functionality_file.feature_file == (
        "AbsaOSS/living-doc/docs/examples/gherkin/liv_doc_func/func-001-validate-password-strength.feature"
    )
    assert [(group.entity_id, len(group.scenarios)) for group in functionality_file.linked_to_functionality] == [
        ("FUNC-001", 4)
    ]
    assert not functionality_file.linked_to_user_story
    assert not functionality_file.unlinked
    assert user_story_file.feature_file == (
        "AbsaOSS/living-doc/docs/examples/gherkin/liv_doc_us/us-001-customer-login.feature"
    )
    assert [(group.entity_id, len(group.scenarios)) for group in user_story_file.linked_to_user_story] == [
        ("US-001", 2)
    ]
    assert not user_story_file.linked_to_functionality
    assert not user_story_file.unlinked
    assert [_without_states(scenario) for scenario in functionality_file.linked_to_functionality[0].scenarios] == [
        _carried(scenario) for scenario in ui_tests.scenarios[:4]
    ]
    assert [_without_states(scenario) for scenario in user_story_file.linked_to_user_story[0].scenarios] == [
        _carried(scenario) for scenario in ui_tests.scenarios[4:]
    ]


def test_scenarios_are_grouped_once_per_entity_and_carried_unchanged(documentation, ui_tests):
    first = _scenario(
        ui_tests,
        "org/repo-a/features/login.feature/first",
        "features/login.feature",
        (("US-001-01", "desktop"), ("US-001-02", "mobile"), ("FUNC-001-01", None), ("US-002-01", None)),
    )
    second = _scenario(
        ui_tests,
        "org/repo-a/features/login.feature/second",
        "features/login.feature",
        (("US-001-03", None),),
    )
    unlinked = _scenario(ui_tests, "org/repo-a/features/login.feature/third", "features/login.feature")
    fallback = _scenario(ui_tests, "SCN-004", "checkout.feature", (("FUNC-002-01", None),))
    other_repository = _scenario(
        ui_tests,
        "org/repo-b/features/login.feature/first",
        "features/login.feature",
        (("US-003-01", None),),
    )
    scenarios = [first, second, unlinked, fallback, other_repository]
    result = _build(documentation, ui_tests.model_copy(update={"scenarios": scenarios}))

    repo_a, fallback_file, repo_b = result.feature_files
    assert [item.feature_file for item in result.feature_files] == [
        "org/repo-a/features/login.feature",
        "checkout.feature",
        "org/repo-b/features/login.feature",
    ]
    assert [group.entity_id for group in repo_a.linked_to_user_story] == ["US-001", "US-002"]
    assert [scenario.scenario_id for scenario in repo_a.linked_to_user_story[0].scenarios] == [
        first.scenario_id,
        second.scenario_id,
    ]
    assert [scenario.scenario_id for scenario in repo_a.linked_to_user_story[1].scenarios] == [first.scenario_id]
    assert [group.entity_id for group in repo_a.linked_to_functionality] == ["FUNC-001"]
    assert [scenario.scenario_id for scenario in repo_a.linked_to_functionality[0].scenarios] == [first.scenario_id]
    assert [scenario.scenario_id for scenario in repo_a.unlinked] == [unlinked.scenario_id]
    assert [group.entity_id for group in fallback_file.linked_to_functionality] == ["FUNC-002"]
    assert [group.entity_id for group in repo_b.linked_to_user_story] == ["US-003"]

    output_scenarios = [
        scenario
        for feature_file in result.feature_files
        for group in (*feature_file.linked_to_user_story, *feature_file.linked_to_functionality)
        for scenario in group.scenarios
    ] + [scenario for feature_file in result.feature_files for scenario in feature_file.unlinked]
    input_by_id = {scenario.scenario_id: _carried(scenario) for scenario in scenarios}
    assert all(_without_states(scenario) == input_by_id[scenario.scenario_id] for scenario in output_scenarios)


def test_non_qualified_scenario_ids_fall_back_and_group_by_native_id(documentation, ui_tests):
    invalid_prefix = _scenario(
        ui_tests,
        "legacy/features/login.feature/scenario-a",
        "features/login.feature",
    )
    unqualified_id = _scenario(ui_tests, "SCN-005", "features/login.feature")
    tests = ui_tests.model_copy(update={"scenarios": [invalid_prefix, unqualified_id]})

    result = _build(documentation, tests)

    assert [item.feature_file for item in result.feature_files] == ["features/login.feature"]
    assert [scenario.scenario_id for scenario in result.feature_files[0].unlinked] == [
        invalid_prefix.scenario_id,
        unqualified_id.scenario_id,
    ]


def test_each_link_carries_its_criterions_state_and_a_link_to_an_unknown_criterion_carries_none(
    documentation, ui_tests
):
    result = _build(documentation, ui_tests)

    functionality_file, user_story_file = result.feature_files
    assert [_links(scenario) for scenario in functionality_file.linked_to_functionality[0].scenarios] == [
        [("FUNC-001-01", "minimum-length", "active")],
        [("FUNC-001-01", "character-classes", "active")],
        [("FUNC-001-01", "no-username", "active")],
        [("FUNC-001-03", "minimum-length", "active")],
    ]
    assert [_links(scenario) for scenario in user_story_file.linked_to_user_story[0].scenarios] == [
        [("US-001-01", None, "active")],
        [("US-001-04", None, "deprecated")],
    ]

    unknown = _scenario(ui_tests, "SCN-006", "checkout.feature", (("US-009-01", None),))
    catalog = _build(documentation, ui_tests.model_copy(update={"scenarios": [unknown]}), view="release")
    assert _links(catalog.feature_files[0].linked_to_user_story[0].scenarios[0]) == [("US-009-01", None, None)]


@pytest.mark.parametrize(
    ("view", "links"),
    [
        (
            "inner",
            [("US-001-02", None, "in_review"), ("US-001-03", None, "planned"), ("US-001-04", None, "deprecated")],
        ),
        ("release", [("US-001-04", None, "deprecated")]),
    ],
)
def test_the_release_view_drops_planned_and_in_review_links_and_the_inner_view_keeps_every_link(
    documentation, ui_tests, view, links
):
    ahead = _scenario(
        ui_tests,
        "org/repo/features/login.feature/ahead",
        "features/login.feature",
        (("US-001-02", None), ("US-001-03", None), ("US-001-04", None)),
    )
    result = _build(
        _with_in_review(documentation, "US-001-02"), ui_tests.model_copy(update={"scenarios": [ahead]}), view
    )

    assert result.document.view == view
    (group,) = result.feature_files[0].linked_to_user_story
    assert group.entity_id == "US-001"
    assert [_links(scenario) for scenario in group.scenarios] == [links]


def test_in_the_release_view_a_scenario_whose_every_link_is_dropped_stays_in_its_group_with_no_link(
    documentation, ui_tests
):
    ahead = _scenario(
        ui_tests,
        "org/repo/features/login.feature/ahead",
        "features/login.feature",
        (("US-001-02", None), ("US-001-03", None), ("FUNC-002-01", None)),
    )
    tests = ui_tests.model_copy(update={"scenarios": [ahead]})

    result = _build(_with_in_review(documentation, "US-001-02"), tests, view="release")

    feature_file = result.feature_files[0]
    assert [
        (group.entity_id, [_links(scenario) for scenario in group.scenarios])
        for group in (
            *feature_file.linked_to_user_story,
            *feature_file.linked_to_functionality,
        )
    ] == [("US-001", [[]]), ("FUNC-002", [[]])]
    assert not feature_file.unlinked


def test_the_new_scenario_fields_pass_through_and_a_files_background_sits_once_on_its_feature_file(
    documentation, ui_tests
):
    background = ["Given the customer is on the login page"]
    under_rule = _scenario(
        ui_tests,
        "org/repo/features/login.feature/under-rule",
        "features/login.feature",
        (("US-001-01", None),),
        line=14,
        rule="A remembered customer skips the form",
        rule_background=["Given the customer was remembered"],
        steps=["When the customer opens the site", "Then the account page shows", '  """', "  Welcome", '  """'],
        background=background,
    )
    plain = _scenario(
        ui_tests,
        "org/repo/features/login.feature/plain",
        "features/login.feature",
        line=30,
        steps=["When the customer signs in", "Then the account page shows"],
        background=background,
    )
    other_file = _scenario(ui_tests, "org/repo/features/other.feature/first", "features/other.feature")

    result = _build(documentation, ui_tests.model_copy(update={"scenarios": [under_rule, plain, other_file]}))

    login, other = result.feature_files
    assert login.background == background
    assert other.background == []
    carried = login.linked_to_user_story[0].scenarios[0]
    assert (carried.line, carried.rule, carried.rule_background, carried.steps) == (
        14,
        "A remembered customer skips the form",
        ["Given the customer was remembered"],
        ["When the customer opens the site", "Then the account page shows", '  """', "  Welcome", '  """'],
    )
    assert "background" not in carried.model_dump()
    assert (login.unlinked[0].line, login.unlinked[0].steps) == (
        30,
        ["When the customer signs in", "Then the account page shows"],
    )


def test_every_warning_of_both_inputs_is_forwarded_the_documentations_first(documentation, ui_tests):
    tests_warning = ContractWarning(code="AUTHORING_ERROR", message="A line was not read.", context="line_no=3")
    tests = ui_tests.model_copy(update={"warnings": [tests_warning]})

    result = _build(documentation, tests)

    assert [warning.code for warning in result.warnings] == [
        *(warning.code for warning in documentation.warnings),
        "AUTHORING_ERROR",
    ]
    assert [warning.context.split(" ", 1)[0] for warning in result.warnings] == [
        "source_input='doc-source-v1.0.0'",
        "source_input='doc-source-v1.0.0'",
        "source_input='ui-tests-v1.0.0'",
    ]


def test_the_source_inputs_are_the_documentation_entry_then_the_tests_entry(documentation, ui_tests):
    result = _build(documentation, ui_tests)

    entries = result.metadata.source_inputs
    assert [entry.schema_version for entry in entries] == ["doc-source-v1.0.0", "ui-tests-v1.0.0"]
    for entry, given in zip(entries, (documentation, ui_tests)):
        assert entry.producer == given.metadata.producer
        assert entry.run == given.metadata.run
        assert entry.source == given.metadata.source
        assert entry.stats == AuditStats.model_validate(given.metadata.stats.model_dump())
    every_record = compute_stats(
        documentation, doc_source_contract.RECORD_ROOTS, documentation.metadata.stats.cardinality
    )
    every_scenario = compute_stats(ui_tests, ui_tests_contract.RECORD_ROOTS, ui_tests.metadata.stats.cardinality)
    assert entries[0].selected_stats == AuditStats.model_validate(every_record.model_dump())
    assert entries[1].selected_stats == AuditStats.model_validate(every_scenario.model_dump())
    assert result.metadata.source == ui_tests.metadata.source


def test_in_the_release_view_the_tests_selected_stats_count_only_the_links_it_keeps(documentation, ui_tests):
    ahead = _scenario(
        ui_tests, "org/repo/features/login.feature/ahead", "features/login.feature", (("US-001-03", None),)
    )
    tests = ui_tests.model_copy(update={"scenarios": [*ui_tests.scenarios, ahead]})

    inner = _build(documentation, tests).metadata.source_inputs[1].selected_stats
    release = _build(documentation, tests, view="release").metadata.source_inputs[1].selected_stats

    assert inner.field_occupancy["scenarios[].acceptance_criteria[].id"] == 7
    assert release.field_occupancy["scenarios[].acceptance_criteria[].id"] == 6
    assert release.cardinality.scenarios == inner.cardinality.scenarios == 7
