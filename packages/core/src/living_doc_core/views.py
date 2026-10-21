# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The view filter every transform runs: the records one view keeps, and the counts of what it kept and dropped
(`living-doc-utilities` `docs/contracts/rendering.md` § Records and presentation).
"""

from collections.abc import Sequence
from typing import get_args

from living_doc_utilities.contracts.common import LifecycleState, View
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.generator_ready import SelectionSummary

# The states the release view drops, for an entity and an acceptance criterion alike. A Feature's state is derived, so
# a Feature is dropped by its derived state; `deprecated` stays.
RELEASE_DROPS: frozenset[LifecycleState] = frozenset({"planned", "in_review"})


def _keeps(view: View, state: LifecycleState) -> bool:
    return view == "inner" or state not in RELEASE_DROPS


def _with_criteria(entity: Entity, view: View) -> Entity:
    criteria = [criterion for criterion in entity.acceptance_criteria if _keeps(view, criterion.state)]
    if len(criteria) == len(entity.acceptance_criteria):
        return entity
    return entity.model_copy(update={"acceptance_criteria": criteria})


def select_records(entities: Sequence[Entity], view: View) -> tuple[list[Entity], SelectionSummary]:
    """
    Select the records one view holds. It selects records only and never edits a field: a kept entity is the input's
    own, or, when the view drops some of its acceptance criteria, a copy holding the others.

    @param entities: The entities, in order.
    @param view: `inner` keeps every record. `release` drops the entities in a `RELEASE_DROPS` state, and the
        acceptance criteria in one of the entities it keeps.
    @return: The kept entities, in input order, and the counts. The acceptance-criteria counts cover kept entities only.
    @raise ValueError: The view is not `inner` or `release`.
    """
    if view not in get_args(View):
        raise ValueError(f"unknown view {view!r}; the views: {', '.join(get_args(View))}")
    kept_entities = [entity for entity in entities if _keeps(view, entity.state)]
    kept = [_with_criteria(entity, view) for entity in kept_entities]
    total_criteria = sum(len(entity.acceptance_criteria) for entity in kept_entities)
    included_criteria = sum(len(entity.acceptance_criteria) for entity in kept)
    summary = SelectionSummary(
        total_entities=len(entities),
        included_entities=len(kept),
        excluded_entities=len(entities) - len(kept),
        total_acceptance_criteria=total_criteria,
        included_acceptance_criteria=included_criteria,
        excluded_acceptance_criteria=total_criteria - included_criteria,
    )
    return kept, summary
