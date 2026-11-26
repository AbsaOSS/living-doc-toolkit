# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Tests that the `normalize-tests` lineage table covers both pinned input contracts, and what it maps."""

from living_doc_utilities.contracts.lineage import Dropped, assert_complete

from living_doc_service_normalize_tests.lineage import LINEAGE_TABLE, USER_STORY_SCENARIO_ROOT


def test_the_lineage_table_accounts_for_every_ui_tests_field():
    assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")


def test_the_lineage_table_accounts_for_every_doc_source_field():
    assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")
    # 54 paths for each of the three entity lists, and 17 for the scenarios.
    assert len(LINEAGE_TABLE.entries) == 3 * 54 + 17


def test_a_files_background_maps_onto_its_feature_file_and_every_other_scenario_path_onto_its_twin():
    scenario_entries = {path: entry for path, entry in LINEAGE_TABLE.entries.items() if path.startswith("scenarios[].")}

    assert scenario_entries.pop("scenarios[].background[]") == "feature_files[].background[]"
    assert scenario_entries == {
        path: f"{USER_STORY_SCENARIO_ROOT}{path.removeprefix('scenarios[].')}" for path in scenario_entries
    }


def test_only_a_criterions_state_is_mapped_from_the_documentation_onto_its_links():
    documentation = {
        path: entry for path, entry in LINEAGE_TABLE.entries.items() if not path.startswith("scenarios[].")
    }
    mapped = {path: entry for path, entry in documentation.items() if isinstance(entry, str)}

    assert mapped == {
        f"{root}[].acceptance_criteria[].state": f"{USER_STORY_SCENARIO_ROOT}acceptance_criteria[].state"
        for root in ("user_stories", "functionalities")
    }
    dropped = [entry for path, entry in documentation.items() if path not in mapped]
    assert all(isinstance(entry, Dropped) and "only the state of each criterion" in entry.reason for entry in dropped)
