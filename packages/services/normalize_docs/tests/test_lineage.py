# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the `normalize-docs` lineage table and the run-time field-loss check (R11).
"""

from datetime import datetime, timezone

import pytest
from living_doc_core.readers import read_documentation
from living_doc_utilities.contracts import doc_source, generator_ready
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.lineage import Dropped, LineageTable, assert_complete
from living_doc_utilities.contracts.schema_export import field_occupancy_paths

from living_doc_service_normalize_docs import service
from living_doc_service_normalize_docs.builder import build_generator_ready
from living_doc_service_normalize_docs.lineage import ENTITY_PATHS, LINEAGE_TABLE


def test_the_table_accounts_for_every_doc_source_path():
    # Act / Assert: raises naming every path the table has no entry for.
    assert_complete(LINEAGE_TABLE, "doc-source-v1.0.0")


def test_the_table_has_no_entry_beyond_the_doc_source_paths():
    assert set(LINEAGE_TABLE.entries) == set(field_occupancy_paths(doc_source.RECORD_ROOTS))
    assert len(LINEAGE_TABLE.entries) == 3 * len(ENTITY_PATHS) == 162


def test_every_path_maps_to_its_own_path_under_content_entities_and_none_is_dropped():
    # Assert
    assert not [entry for entry in LINEAGE_TABLE.entries.values() if isinstance(entry, Dropped)]
    for input_path, output_path in LINEAGE_TABLE.entries.items():
        assert output_path == "content.entities[]." + input_path.split("[].", 1)[1]
    assert set(LINEAGE_TABLE.entries.values()) == set(field_occupancy_paths(generator_ready.RECORD_ROOTS))


def test_a_table_missing_a_path_fails_the_completeness_check_naming_it():
    # Arrange
    entries = dict(LINEAGE_TABLE.entries)
    del entries["features[].stub_reason"]

    # Act / Assert
    with pytest.raises(AssertionError, match=r"\['features\[\]\.stub_reason'\]"):
        assert_complete(LineageTable(entries), "doc-source-v1.0.0")


def test_a_field_the_table_does_not_know_never_stops_a_run(monkeypatch, doc_source, run_command):
    # Arrange: the table forgets a field the input fills; only the tests check completeness, never the command.
    entries = {path: entry for path, entry in LINEAGE_TABLE.entries.items() if not path.endswith("].purpose")}
    monkeypatch.setattr(service, "LINEAGE_TABLE", LineageTable(entries))

    # Act
    result = run_command(doc_source)

    # Assert
    assert len(result.content.entities) == 5


def _build(doc_source, view: str):
    return build_generator_ready(
        read_documentation(doc_source),
        view=view,
        generated_at=datetime(2026, 10, 21, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize("view", ["inner", "release"])
def test_the_field_loss_check_passes_over_the_fixture(doc_source, view):
    # Act / Assert: the release view drops FUNC-002, the one functionality with a `not_in_scope`, and every planned
    # criterion; the check compares against the kept records, so that is no loss.
    service.check_no_field_loss(_build(doc_source, view))


def test_the_field_loss_check_names_each_lost_path(doc_source):
    # Arrange: every entity loses its `purpose`, which both Features fill.
    result = _build(doc_source, "inner")
    result.content.entities = [entity.model_copy(update={"purpose": None}) for entity in result.content.entities]

    # Act
    with pytest.raises(ContractError) as error:
        service.check_no_field_loss(result)

    # Assert
    assert error.value.code is Code.FIELD_LOSS
    assert error.value.message == (
        "'features[].purpose' had occupancy 2 on input but its mapped output path 'content.entities[].purpose' has "
        "occupancy 0"
    )
