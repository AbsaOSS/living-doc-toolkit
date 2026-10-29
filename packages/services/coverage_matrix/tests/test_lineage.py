# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Tests that the `coverage-matrix` lineage table covers both pinned input contracts, and what it maps."""

from living_doc_utilities.contracts.lineage import Dropped, assert_complete

from living_doc_service_coverage_matrix.lineage import ENTITY_PATHS, LINEAGE_TABLE


def test_the_lineage_table_accounts_for_every_doc_source_field():
    assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")


def test_the_lineage_table_accounts_for_every_ui_tests_field():
    assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")
    # 54 paths for each of the three entity lists, and 12 for the scenarios.
    assert len(LINEAGE_TABLE.entries) == 3 * 54 + 12


def test_only_identity_criterion_aspect_keyword_and_scenario_id_paths_are_mapped():
    mapped = {path: entry for path, entry in LINEAGE_TABLE.entries.items() if isinstance(entry, str)}

    assert mapped == {
        **{
            f"{root}[].{path}": output
            for root in ("user_stories", "functionalities")
            for path, output in (
                ("entity_id", "entities[].entity_id"),
                ("type", "entities[].type"),
                ("title", "entities[].title"),
                ("state", "entities[].state"),
                ("acceptance_criteria[].id", "entities[].acceptance_criteria[].ac_id"),
                ("acceptance_criteria[].state", "entities[].acceptance_criteria[].state"),
                ("acceptance_criteria[].aspect[]", "entities[].acceptance_criteria[].aspects[].aspect"),
                ("acceptance_criteria[].placeholder_values", "entities[].acceptance_criteria[].keyword"),
            )
        },
        "scenarios[].scenario_id": "entities[].acceptance_criteria[].scenario_ids[]",
    }


def test_every_feature_path_is_dropped_because_the_matrix_has_no_feature_entity():
    entries = [LINEAGE_TABLE.entries[f"features[].{path}"] for path in ENTITY_PATHS]

    assert all(isinstance(entry, Dropped) and "no Feature entity" in entry.reason for entry in entries)


def test_a_links_id_and_aspect_are_dropped_because_they_only_route_its_scenario():
    link_id = LINEAGE_TABLE.entries["scenarios[].acceptance_criteria[].id"]
    link_aspect = LINEAGE_TABLE.entries["scenarios[].acceptance_criteria[].aspect"]

    assert isinstance(link_id, Dropped) and "which criterion's row lists its scenario" in link_id.reason
    assert isinstance(link_aspect, Dropped) and "which aspect of the criterion's row lists its scenario" in (
        link_aspect.reason
    )


def test_every_dropped_path_says_why():
    dropped = [entry for entry in LINEAGE_TABLE.entries.values() if isinstance(entry, Dropped)]

    assert len(dropped) == len(LINEAGE_TABLE.entries) - 17
    assert all(entry.reason for entry in dropped)
