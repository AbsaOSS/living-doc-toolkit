# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for typed catalog construction, grouping, ordering, and envelope contents."""

from datetime import datetime, timezone
from typing import get_type_hints

from living_doc_utilities.contracts.ui_test_catalog import UiTestCatalogResult
from living_doc_utilities.contracts.ui_tests import AcLink, Scenario, UITestsResult

from living_doc_service_normalize_tests.builder import build_ui_test_catalog

GENERATED_AT = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def _scenario(
    tests: UITestsResult,
    scenario_id: str,
    native_id: str,
    links: tuple[tuple[str, str | None], ...] = (),
) -> Scenario:
    template = tests.scenarios[0]
    return template.model_copy(
        update={
            "scenario_id": scenario_id,
            "source_ref": template.source_ref.model_copy(update={"native_id": native_id}),
            "acceptance_criteria": [AcLink(id=identifier, aspect=aspect) for identifier, aspect in links],
        }
    )


def test_the_builder_is_typed_on_the_contract_models_in_and_out():
    hints = get_type_hints(build_ui_test_catalog)

    assert hints["tests"] is UITestsResult
    assert hints["return"] is UiTestCatalogResult


def test_the_builder_takes_and_returns_contract_model_instances(ui_tests):
    result = build_ui_test_catalog(ui_tests, generated_at=GENERATED_AT)

    assert isinstance(ui_tests, UITestsResult)
    assert isinstance(result, UiTestCatalogResult)


def test_the_fixture_groups_feature_files_and_entities_in_input_order(ui_tests):
    result = build_ui_test_catalog(ui_tests, generated_at=GENERATED_AT)

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
    assert functionality_file.linked_to_functionality[0].scenarios == ui_tests.scenarios[:4]
    assert user_story_file.linked_to_user_story[0].scenarios == ui_tests.scenarios[4:]


def test_scenarios_are_grouped_once_per_entity_and_preserved_unchanged(ui_tests):
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
    result = build_ui_test_catalog(ui_tests.model_copy(update={"scenarios": scenarios}), generated_at=GENERATED_AT)

    repo_a, fallback_file, repo_b = result.feature_files
    assert [item.feature_file for item in result.feature_files] == [
        "org/repo-a/features/login.feature",
        "checkout.feature",
        "org/repo-b/features/login.feature",
    ]
    assert [group.entity_id for group in repo_a.linked_to_user_story] == ["US-001", "US-002"]
    assert repo_a.linked_to_user_story[0].scenarios == [first, second]
    assert repo_a.linked_to_user_story[1].scenarios == [first]
    assert [group.entity_id for group in repo_a.linked_to_functionality] == ["FUNC-001"]
    assert repo_a.linked_to_functionality[0].scenarios == [first]
    assert repo_a.unlinked == [unlinked]
    assert [group.entity_id for group in fallback_file.linked_to_functionality] == ["FUNC-002"]
    assert [group.entity_id for group in repo_b.linked_to_user_story] == ["US-003"]

    output_scenarios = [
        scenario
        for feature_file in result.feature_files
        for group in (*feature_file.linked_to_user_story, *feature_file.linked_to_functionality)
        for scenario in group.scenarios
    ] + [scenario for feature_file in result.feature_files for scenario in feature_file.unlinked]
    input_by_id = {scenario.scenario_id: scenario.model_dump() for scenario in scenarios}
    assert all(scenario.model_dump() == input_by_id[scenario.scenario_id] for scenario in output_scenarios)


def test_non_qualified_scenario_ids_fall_back_and_group_by_native_id(ui_tests):
    invalid_prefix = _scenario(
        ui_tests,
        "legacy/features/login.feature/scenario-a",
        "features/login.feature",
    )
    unqualified_id = _scenario(ui_tests, "SCN-005", "features/login.feature")
    tests = ui_tests.model_copy(update={"scenarios": [invalid_prefix, unqualified_id]})

    result = build_ui_test_catalog(tests, generated_at=GENERATED_AT)

    assert [item.feature_file for item in result.feature_files] == ["features/login.feature"]
    assert result.feature_files[0].unlinked == [invalid_prefix, unqualified_id]
