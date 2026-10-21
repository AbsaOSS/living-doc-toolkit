# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for the view filter.
"""

import pytest
from living_doc_utilities.contracts.common import AcceptanceCriterion, SourceRef
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.generator_ready import SelectionSummary

from living_doc_core.views import RELEASE_DROPS, select_records

_TYPES = {"US": "DocumentedUserStory", "FEAT": "DocumentedFeature", "FUNC": "DocumentedFunctionality"}


def _criterion(ac_id: str, state: str) -> AcceptanceCriterion:
    removal = {"removal_planned": "2.0.0"} if state == "deprecated" else {}
    version = {} if state == "planned" else {"version": "1.0.0"}
    return AcceptanceCriterion(id=ac_id, state=state, description=f"{ac_id} holds.", **version, **removal)


def _entity(entity_id: str, state: str, *criteria: str) -> Entity:
    """An entity in `state`, with one criterion per given state, numbered from 01."""
    entity_type = _TYPES[entity_id.split("-")[0]]
    return Entity(
        entity_id=entity_id,
        source_ref=SourceRef(
            system="GitHub",
            native_id=entity_id,
            native_type="feature-file",
            url=f"https://github.com/AbsaOSS/living-doc/issues/{entity_id}",
            tracker_state="committed",
        ),
        type=entity_type,
        title=entity_id,
        state=state,
        state_origin="derived" if entity_type == "DocumentedFeature" else "authored",
        acceptance_criteria=[
            _criterion(f"{entity_id}-{index:02d}", ac_state) for index, ac_state in enumerate(criteria, start=1)
        ],
    )


ENTITIES = [
    _entity("US-001", "active", "active", "planned", "in_review", "deprecated"),
    _entity("US-002", "planned", "active"),
    _entity("US-003", "in_review", "active", "active"),
    _entity("US-004", "deprecated", "deprecated"),
    _entity("FEAT-001", "active"),
    _entity("FEAT-002", "planned"),
    _entity("FEAT-003", "in_review"),
    _entity("FEAT-004", "deprecated"),
    _entity("FUNC-001", "active", "planned", "active"),
    _entity("FUNC-002", "planned", "planned"),
    _entity("FUNC-003", "in_review"),
    _entity("FUNC-004", "deprecated", "active"),
]


def _ids(entities: list[Entity]) -> list[str]:
    return [entity.entity_id for entity in entities]


def _criteria(entities: list[Entity]) -> list[str]:
    return [criterion.id for entity in entities for criterion in entity.acceptance_criteria]


def test_the_release_view_drops_planned_and_in_review_states():
    assert RELEASE_DROPS == {"planned", "in_review"}


def test_the_inner_view_keeps_every_record_as_it_is():
    # Act
    kept, summary = select_records(ENTITIES, "inner")

    # Assert
    assert all(kept_entity is entity for kept_entity, entity in zip(kept, ENTITIES, strict=True))
    assert summary == SelectionSummary(
        total_entities=12,
        included_entities=12,
        excluded_entities=0,
        total_acceptance_criteria=12,
        included_acceptance_criteria=12,
        excluded_acceptance_criteria=0,
    )


def test_the_release_view_drops_planned_and_in_review_entities_and_keeps_deprecated_ones():
    # Act
    kept, _ = select_records(ENTITIES, "release")

    # Assert: the Features are dropped by their derived state, as the others by their authored one.
    assert _ids(kept) == ["US-001", "US-004", "FEAT-001", "FEAT-004", "FUNC-001", "FUNC-004"]


def test_the_release_view_drops_planned_and_in_review_criteria_of_the_entities_it_keeps():
    # Act
    kept, _ = select_records(ENTITIES, "release")

    # Assert
    assert _criteria(kept) == ["US-001-01", "US-001-04", "US-004-01", "FUNC-001-02", "FUNC-004-01"]
    assert {criterion.state for entity in kept for criterion in entity.acceptance_criteria} == {"active", "deprecated"}


def test_the_release_counts_cover_the_criteria_of_kept_entities_only():
    # Act
    _, summary = select_records(ENTITIES, "release")

    # Assert: US-001's 4, US-004's 1, FUNC-001's 2 and FUNC-004's 1 are counted; a dropped entity's never are.
    assert summary == SelectionSummary(
        total_entities=12,
        included_entities=6,
        excluded_entities=6,
        total_acceptance_criteria=8,
        included_acceptance_criteria=5,
        excluded_acceptance_criteria=3,
    )


def test_the_filter_selects_records_and_never_edits_a_field():
    # Act
    kept, _ = select_records(ENTITIES, "release")

    # Assert: an entity whose criteria all stay is the input's own; the others differ only in the criteria list.
    by_id = {entity.entity_id: entity for entity in ENTITIES}
    for entity in kept:
        original = by_id[entity.entity_id]
        if entity.acceptance_criteria == original.acceptance_criteria:
            assert entity is original
        assert entity.model_dump(exclude={"acceptance_criteria"}) == original.model_dump(
            exclude={"acceptance_criteria"}
        )
        assert all(criterion in original.acceptance_criteria for criterion in entity.acceptance_criteria)
    assert [len(entity.acceptance_criteria) for entity in ENTITIES] == [4, 1, 2, 1, 0, 0, 0, 0, 2, 1, 0, 1]


def test_no_entities_select_nothing():
    # Act
    kept, summary = select_records([], "release")

    # Assert
    assert kept == []
    assert summary.total_entities == summary.total_acceptance_criteria == 0


def test_an_unknown_view_is_a_value_error():
    with pytest.raises(ValueError, match="unknown view 'Release'; the views: inner, release"):
        select_records(ENTITIES, "Release")
