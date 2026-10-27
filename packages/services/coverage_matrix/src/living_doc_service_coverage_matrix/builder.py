# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` builder: a validated documentation input and tests input to a coverage matrix, counted per
acceptance criterion, with no I/O or environment reads.
"""

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import TypeGuard, get_args

from living_doc_core.envelope import PRODUCER_NAME, TOOLKIT_VERSION, forwarded
from living_doc_utilities.contracts import doc_source, ui_tests
from living_doc_utilities.contracts.common import LifecycleState, View
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.coverage_matrix import (
    AcCoverage,
    CountedState,
    CoverageMatrixResult,
    CoverageSummary,
    Document,
    EntityCoverage,
    PlannedSummary,
)
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import (
    AuditStats,
    Cardinality,
    Metadata,
    Producer,
    Source,
    SourceInputEntry,
    Stats,
)
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_tests import UITestsResult


def _is_counted(state: LifecycleState) -> TypeGuard[CountedState]:
    """Whether a criterion in `state` gets a coverage row: `active` and `deprecated` do, in both views."""
    return state in get_args(CountedState)


def _matrix_entities(documentation: DocSourceResult) -> list[Entity]:
    """The entities the matrix holds: every User Story, then every Functionality, each list in input order."""
    return [*documentation.user_stories, *documentation.functionalities]


def _linked_scenarios(tests: UITestsResult) -> dict[str, list[str]]:
    """Each linked criterion id with the ids of the scenarios that link it, each once, in input order."""
    scenario_ids: dict[str, list[str]] = {}
    for scenario in tests.scenarios:
        for link in scenario.acceptance_criteria:
            linked = scenario_ids.setdefault(link.id, [])
            if scenario.scenario_id not in linked:
                linked.append(scenario.scenario_id)
    return scenario_ids


def _entity_coverage(entity: Entity, scenario_ids: Mapping[str, list[str]]) -> EntityCoverage:
    """One entity's row per counted criterion, in the entity's order, with the summary of those rows."""
    if entity.type == "DocumentedFeature":
        # `doc-source` holds Features in `features[]` only, which the matrix does not read.
        raise ValueError(f"entity {entity.entity_id!r} is a Feature, and the coverage matrix has no Feature entity")
    rows = []
    for criterion in entity.acceptance_criteria:
        if _is_counted(criterion.state):
            linked = list(scenario_ids.get(criterion.id, []))
            rows.append(
                AcCoverage(
                    ac_id=criterion.id,
                    state=criterion.state,
                    status="covered" if linked else "not_covered",
                    scenario_ids=linked,
                )
            )
    return EntityCoverage(
        entity_id=entity.entity_id,
        type=entity.type,
        title=entity.title,
        state=entity.state,
        acceptance_criteria=rows,
        summary=CoverageSummary.from_rows(rows),
    )


def _planned_summary(entities: Iterable[Entity]) -> PlannedSummary:
    """The `planned` criteria: by target version, in the order first met, or in the backlog without one."""
    backlog = 0
    by_target_version: dict[str, int] = {}
    for entity in entities:
        for criterion in entity.acceptance_criteria:
            if criterion.state != "planned":
                continue
            if criterion.version is None:
                backlog += 1
            else:
                by_target_version[criterion.version] = by_target_version.get(criterion.version, 0) + 1
    return PlannedSummary(
        total=backlog + sum(by_target_version.values()), backlog=backlog, by_target_version=by_target_version
    )


def _source(documentation: DocSourceResult, tests: UITestsResult) -> Source:
    """The documentation input's `source`, with each of the tests input's systems it does not name appended once."""
    systems = list(documentation.metadata.source.systems)
    for system in tests.metadata.source.systems:
        if system not in systems:
            systems.append(system)
    return documentation.metadata.source.model_copy(update={"systems": systems})


def _counted_selection(documentation: DocSourceResult) -> DocSourceResult:
    """
    The records the matrix counts: the User Stories and Functionalities, each with only its `active` and `deprecated`
    criteria, and no Feature. Its stats are the documentation entry's `selected_stats`.
    """

    def counted(entities: list[Entity]) -> list[Entity]:
        return [
            entity.model_copy(
                update={
                    "acceptance_criteria": [
                        criterion for criterion in entity.acceptance_criteria if _is_counted(criterion.state)
                    ]
                }
            )
            for entity in entities
        ]

    return documentation.model_copy(
        update={
            "user_stories": counted(documentation.user_stories),
            "features": [],
            "functionalities": counted(documentation.functionalities),
        }
    )


def _documentation_entry(documentation: DocSourceResult) -> SourceInputEntry:
    selected = compute_stats(
        _counted_selection(documentation), doc_source.RECORD_ROOTS, documentation.metadata.stats.cardinality
    )
    return SourceInputEntry(
        schema_version=documentation.schema_version,
        producer=documentation.metadata.producer,
        run=documentation.metadata.run,
        source=documentation.metadata.source,
        stats=AuditStats.model_validate(documentation.metadata.stats.model_dump()),
        selected_stats=AuditStats.model_validate(selected.model_dump()),
    )


def _tests_entry(tests: UITestsResult) -> SourceInputEntry:
    selected = compute_stats(tests, ui_tests.RECORD_ROOTS, tests.metadata.stats.cardinality)
    return SourceInputEntry(
        schema_version=tests.schema_version,
        producer=tests.metadata.producer,
        run=tests.metadata.run,
        source=tests.metadata.source,
        stats=AuditStats.model_validate(tests.metadata.stats.model_dump()),
        selected_stats=AuditStats.model_validate(selected.model_dump()),
    )


def build_coverage_matrix(
    documentation: DocSourceResult, tests: UITestsResult, *, view: View, generated_at: datetime
) -> CoverageMatrixResult:
    """
    Build `coverage-matrix` from one documentation input and one tests input: an entity per User Story and
    Functionality, a row per counted criterion with the scenarios that link it, the summaries, both inputs recorded in
    `metadata.source_inputs[]` and every input warning forwarded.

    @param documentation: The validated documentation input.
    @param tests: The validated tests input.
    @param view: `document.view`, `inner` or `release`; it changes no row and no count.
    @param generated_at: The write time.
    @return: The output model. Its `metadata.run` is empty, for the caller to set to the CI run. Its `metadata.stats`
        holds only the counts a caller reports, all 0 for a transform, and `write_artifact` computes the rest.
    """
    scenario_ids = _linked_scenarios(tests)
    documented = _matrix_entities(documentation)
    entities = [_entity_coverage(entity, scenario_ids) for entity in documented]

    return CoverageMatrixResult(
        metadata=Metadata(
            producer=Producer(
                name=PRODUCER_NAME, version=TOOLKIT_VERSION, utilities_version=installed_utilities_version()
            ),
            source=_source(documentation, tests),
            generated_at=generated_at,
            stats=Stats(cardinality=Cardinality()),
            source_inputs=[_documentation_entry(documentation), _tests_entry(tests)],
        ),
        warnings=[
            *(forwarded(warning, documentation.schema_version) for warning in documentation.warnings),
            *(forwarded(warning, tests.schema_version) for warning in tests.warnings),
        ],
        document=Document(view=view),
        entities=entities,
        planned_summary=_planned_summary(documented),
        summary=CoverageSummary.from_rows(row for entity in entities for row in entity.acceptance_criteria),
    )
