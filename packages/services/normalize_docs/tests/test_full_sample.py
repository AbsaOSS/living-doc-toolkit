# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
R12 check 3: the transform over `living-doc-utilities`' unfiltered full sample of `doc-source-v1.0.0`, in every view,
loses no field.

The sample repeats its four entities in each of the three lists, so the shared input validation would stop it with
`DUPLICATE_ENTITY_ID`; it is handed to the builder as the validated model instead, and the rest runs as the command
runs it: the field-loss check, the write and a read back.
"""

import pytest
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult
from living_doc_utilities.contracts.io import read_artifact, write_artifact
from living_doc_utilities.contracts.testing import full_sample

from living_doc_service_normalize_docs.builder import build_generator_ready
from living_doc_service_normalize_docs.lineage import LINEAGE_TABLE
from living_doc_service_normalize_docs.service import check_no_field_loss


def _transformed(tmp_path, view: str) -> GeneratorReadyResult:
    sample = full_sample("doc-source-v1.0.0")
    assert isinstance(sample, DocSourceResult)
    result = build_generator_ready(sample, view=view, generated_at=sample.metadata.generated_at)
    check_no_field_loss(result)
    write_artifact(result, tmp_path / "generator-ready.json")
    written = read_artifact(tmp_path / "generator-ready.json", expected="generator-ready")
    assert isinstance(written, GeneratorReadyResult)
    return written


def test_the_sample_holds_planned_criteria_and_is_not_filtered_before_the_transform():
    # Assert: the transform, not the test, filters.
    sample = full_sample("doc-source-v1.0.0")
    states = {criterion.state for entity in sample.user_stories for criterion in entity.acceptance_criteria}
    assert "planned" in states


@pytest.mark.parametrize("view", ["inner", "release"])
def test_the_full_sample_loses_no_field_in_either_view(tmp_path, view):
    # Act / Assert: `check_no_field_loss` raises FIELD_LOSS on a loss.
    assert _transformed(tmp_path, view).document.view == view


def test_in_the_inner_view_every_mapped_path_has_data(tmp_path):
    # Act
    occupancy = _transformed(tmp_path, "inner").metadata.stats.field_occupancy

    # Assert
    empty = sorted({path for path in LINEAGE_TABLE.entries.values() if occupancy[path] == 0})
    assert empty == []


def test_the_release_view_holds_no_planned_or_in_review_record(tmp_path):
    # Act
    result = _transformed(tmp_path, "release")

    # Assert
    entities = result.content.entities
    assert {entity.state for entity in entities} <= {"active", "deprecated"}
    assert {criterion.state for entity in entities for criterion in entity.acceptance_criteria} <= {
        "active",
        "deprecated",
    }
    assert result.document.selection_summary.excluded_acceptance_criteria == 6
