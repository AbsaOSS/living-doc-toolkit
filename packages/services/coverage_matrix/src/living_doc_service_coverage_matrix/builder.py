# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` builder: a validated documentation input and tests input to a coverage matrix, counted per
declared aspect of each acceptance criterion, with a warning per scenario link it does not count as written, and no
I/O or environment reads.
"""

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import TypeGuard, get_args

from living_doc_core.envelope import PRODUCER_NAME, TOOLKIT_VERSION, forwarded
from living_doc_utilities.contracts import doc_source, ui_tests
from living_doc_utilities.contracts.codes import Code
from living_doc_utilities.contracts.common import AcceptanceCriterion, LifecycleState, View
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.coverage_matrix import (
    AcCoverage,
    AspectCoverage,
    CountedState,
    CoverageMatrixResult,
    CoverageStatus,
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
    ContractWarning,
    Metadata,
    Producer,
    Source,
    SourceInputEntry,
    Stats,
)
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_tests import AcLink, UITestsResult

# One scenario link to a criterion: the scenario's id and the link's aspect, `None` for a bare `@AC:<id>` tag.
Link = tuple[str, str | None]


def _is_counted(state: LifecycleState) -> TypeGuard[CountedState]:
    """Whether a criterion in `state` gets a coverage row: `active` and `deprecated` do, in both views."""
    return state in get_args(CountedState)


def _matrix_entities(documentation: DocSourceResult) -> list[Entity]:
    """The entities the matrix holds: every User Story, then every Functionality, each list in input order."""
    return [*documentation.user_stories, *documentation.functionalities]


def _linked_scenarios(tests: UITestsResult) -> dict[str, list[Link]]:
    """Each linked criterion id with every link to it, in input order."""
    links: dict[str, list[Link]] = {}
    for scenario in tests.scenarios:
        for link in scenario.acceptance_criteria:
            links.setdefault(link.id, []).append((scenario.scenario_id, link.aspect))
    return links


def _once(scenario_ids: Iterable[str]) -> list[str]:
    """`scenario_ids` with each id once, in the order first met."""
    return list(dict.fromkeys(scenario_ids))


def _aspect_coverage(aspect: str, links: Sequence[Link]) -> AspectCoverage:
    """One declared aspect, with the scenarios whose link names it or, bare, names every aspect."""
    scenario_ids = _once(scenario_id for scenario_id, linked in links if linked in (None, aspect))
    return AspectCoverage(aspect=aspect, status="covered" if scenario_ids else "not_covered", scenario_ids=scenario_ids)


def _row(criterion: AcceptanceCriterion, state: CountedState, links: Sequence[Link]) -> AcCoverage:
    """
    A counted criterion's row, `state` being its state. With aspects, the row has one per declared value, in declared
    order, its status follows them, and its own `scenario_ids` stays empty; a link to an undeclared aspect counts
    nowhere. Without, every link covers it, one with an aspect too.
    """
    if not criterion.aspect:
        scenario_ids = _once(scenario_id for scenario_id, _aspect in links)
        return AcCoverage(
            ac_id=criterion.id,
            state=state,
            status="covered" if scenario_ids else "not_covered",
            scenario_ids=scenario_ids,
        )
    aspects = [_aspect_coverage(aspect, links) for aspect in criterion.aspect]
    covered = sum(1 for aspect in aspects if aspect.status == "covered")
    status: CoverageStatus = "covered" if covered == len(aspects) else "partially_covered" if covered else "not_covered"
    return AcCoverage(
        ac_id=criterion.id,
        state=state,
        status=status,
        # A keyword criterion keeps its one name as `placeholder_values`' key; an `Aspect:` one has none.
        keyword=next(iter(criterion.placeholder_values), None),
        aspects=aspects,
    )


def _entity_coverage(entity: Entity, links: Mapping[str, list[Link]]) -> EntityCoverage:
    """One entity's row per counted criterion, in the entity's order, with the summary of those rows."""
    if entity.type == "DocumentedFeature":
        # `doc-source` holds Features in `features[]` only, which the matrix does not read.
        raise ValueError(f"entity {entity.entity_id!r} is a Feature, and the coverage matrix has no Feature entity")
    rows = [
        _row(criterion, criterion.state, links.get(criterion.id, []))
        for criterion in entity.acceptance_criteria
        if _is_counted(criterion.state)
    ]
    return EntityCoverage(
        entity_id=entity.entity_id,
        type=entity.type,
        title=entity.title,
        state=entity.state,
        acceptance_criteria=rows,
        summary=CoverageSummary.from_rows(rows),
    )


def _warning(code: Code, message: str, scenario_id: str, ac_id: str, aspect: str | None = None) -> ContractWarning:
    """A link warning: on the linked criterion and its entity, the id without its last `-<n>`. A collector fills
    `line_no`, `path` and `source_url`, so they stay unset."""
    context = f"scenario_id={scenario_id!r}" if aspect is None else f"scenario_id={scenario_id!r} aspect={aspect!r}"
    return ContractWarning(
        code=code.name, message=message, context=context, entity_id=ac_id.rsplit("-", 1)[0], ac_id=ac_id
    )


def _link_warning(scenario_id: str, link: AcLink, criterion: AcceptanceCriterion | None) -> ContractWarning | None:
    """The warning for one link, or `None` when the matrix counts it as written. `criterion` is the one the link names,
    `None` when no User Story or Functionality has it."""
    linked = f"Scenario {scenario_id!r} links acceptance criterion {link.id!r}"
    if criterion is None:
        return _warning(
            Code.STALE_AC_REF,
            f"{linked}, which no User Story or Functionality in the documentation has: the link counts nowhere. Fix "
            "the tag, or document the criterion.",
            scenario_id,
            link.id,
        )
    # Whatever the link's aspect: the criterion has no row to check it against.
    if criterion.state == "planned":
        return _warning(
            Code.PLANNED_AC_HAS_TESTS,
            f"{linked}, which is planned: the matrix counts no planned criterion, so the link counts nowhere until "
            "the criterion is active.",
            scenario_id,
            link.id,
        )
    if criterion.state == "in_review":
        return _warning(
            Code.IN_REVIEW_AC_HAS_TESTS,
            f"{linked}, which is in review: the matrix counts no criterion in review, so the link counts nowhere. If "
            "its work has merged, set the criterion active.",
            scenario_id,
            link.id,
        )
    if link.aspect is None or link.aspect in criterion.aspect:
        return None
    linked_aspect = f"Scenario {scenario_id!r} links aspect {link.aspect!r} of acceptance criterion {link.id!r}"
    if criterion.aspect:
        effect = "which the criterion does not declare: the link counts nowhere. Fix the tag, or declare the aspect."
    else:
        # The scenario names the criterion, and a criterion without aspects has one thing to cover.
        effect = (
            "which declares no aspects: the link covers the whole criterion, as a bare one does. Drop the aspect from "
            "the tag, or declare the criterion's aspects."
        )
    return _warning(Code.STALE_AC_REF, f"{linked_aspect}, {effect}", scenario_id, link.id, link.aspect)


def _link_warnings(entities: Iterable[Entity], tests: UITestsResult) -> list[ContractWarning]:
    """
    A warning for each link the matrix does not count as written: `STALE_AC_REF` for an unknown criterion or an
    undeclared aspect, `PLANNED_AC_HAS_TESTS` and `IN_REVIEW_AC_HAS_TESTS` for a criterion with no row. One per
    scenario and criterion, and per aspect for an undeclared one, in scenario order, then link order.
    """
    criteria = {criterion.id: criterion for entity in entities for criterion in entity.acceptance_criteria}
    warnings: dict[tuple[str | None, str | None], ContractWarning] = {}
    for scenario in tests.scenarios:
        for link in scenario.acceptance_criteria:
            warning = _link_warning(scenario.scenario_id, link, criteria.get(link.id))
            # `ac_id` names the criterion, and `context` the scenario and any undeclared aspect.
            if warning is not None:
                warnings.setdefault((warning.ac_id, warning.context), warning)
    return list(warnings.values())


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
    Functionality, a row per counted criterion with the scenarios that link it, per declared aspect where it has
    aspects, the summaries, both inputs recorded in `metadata.source_inputs[]`, every input warning forwarded, then a
    warning per link the matrix does not count as written.

    @param documentation: The validated documentation input.
    @param tests: The validated tests input.
    @param view: `document.view`, `inner` or `release`; it changes no row and no count.
    @param generated_at: The write time.
    @return: The output model. Its `metadata.run` is empty, for the caller to set to the CI run. Its `metadata.stats`
        holds only the counts a caller reports, all 0 for a transform, and `write_artifact` computes the rest.
    """
    links = _linked_scenarios(tests)
    documented = _matrix_entities(documentation)
    entities = [_entity_coverage(entity, links) for entity in documented]

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
            *_link_warnings(documented, tests),
        ],
        document=Document(view=view),
        entities=entities,
        planned_summary=_planned_summary(documented),
        summary=CoverageSummary.from_rows(row for entity in entities for row in entity.acceptance_criteria),
    )
