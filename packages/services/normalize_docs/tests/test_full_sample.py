# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
R12 check 3: `normalize-docs` over `living-doc-utilities`' unfiltered full sample of `doc-source-v1.0.0`, written to a
file with `write_artifact` and read through the shared input validation, loses no field in either view.
"""

import pytest
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.generator_ready import SelectionSummary
from living_doc_utilities.contracts.io import write_artifact
from living_doc_utilities.contracts.testing import full_sample

from living_doc_service_normalize_docs.lineage import LINEAGE_TABLE

# The states the release view drops, for an entity and an acceptance criterion alike.
RELEASE_DROPS = {"planned", "in_review"}


def _sample() -> DocSourceResult:
    sample = full_sample("doc-source-v1.0.0")
    assert isinstance(sample, DocSourceResult)
    return sample


def _entities(sample: DocSourceResult) -> list[Entity]:
    return [*sample.user_stories, *sample.features, *sample.functionalities]


@pytest.fixture(name="sample_file")
def _sample_file(tmp_path):
    """The full sample, written as a collector writes `doc-source.json`."""
    path = tmp_path / "in" / "doc-source.json"
    write_artifact(_sample(), path)
    return path


def test_the_sample_holds_planned_criteria_and_is_not_filtered_before_the_transform():
    # Assert: the transform, not the test, filters.
    states = {criterion.state for entity in _entities(_sample()) for criterion in entity.acceptance_criteria}
    assert "planned" in states


@pytest.mark.parametrize("view", ["inner", "release"])
def test_the_full_sample_loses_no_field_in_either_view(sample_file, run_command, view):
    # Act / Assert: the command raises FIELD_LOSS on a loss, and writes no file.
    assert run_command(sample_file, view=view).document.view == view


def test_in_the_inner_view_every_mapped_path_has_data(sample_file, run_command):
    # Act
    occupancy = run_command(sample_file, view="inner").metadata.stats.field_occupancy

    # Assert
    empty = sorted({path for path in LINEAGE_TABLE.entries.values() if occupancy[path] == 0})
    assert empty == []


def test_in_the_inner_view_the_selection_summary_counts_every_record(sample_file, run_command):
    # Arrange
    entities = _entities(_sample())
    criteria = sum(len(entity.acceptance_criteria) for entity in entities)

    # Act
    summary = run_command(sample_file, view="inner").document.selection_summary

    # Assert
    assert summary == SelectionSummary(
        total_entities=len(entities),
        included_entities=len(entities),
        excluded_entities=0,
        total_acceptance_criteria=criteria,
        included_acceptance_criteria=criteria,
        excluded_acceptance_criteria=0,
    )


def test_the_release_view_holds_no_planned_or_in_review_record(sample_file, run_command):
    # Arrange: what the release view keeps, derived from the sample.
    entities = _entities(_sample())
    kept = [entity for entity in entities if entity.state not in RELEASE_DROPS]
    criteria = [criterion for entity in kept for criterion in entity.acceptance_criteria]
    dropped = sum(criterion.state in RELEASE_DROPS for criterion in criteria)
    assert dropped > 0

    # Act
    result = run_command(sample_file, view="release")

    # Assert
    written = result.content.entities
    assert [entity.entity_id for entity in written] == [entity.entity_id for entity in kept]
    assert not {entity.state for entity in written} & RELEASE_DROPS
    assert not {criterion.state for entity in written for criterion in entity.acceptance_criteria} & RELEASE_DROPS
    assert result.document.selection_summary == SelectionSummary(
        total_entities=len(entities),
        included_entities=len(kept),
        excluded_entities=len(entities) - len(kept),
        total_acceptance_criteria=len(criteria),
        included_acceptance_criteria=len(criteria) - dropped,
        excluded_acceptance_criteria=dropped,
    )
