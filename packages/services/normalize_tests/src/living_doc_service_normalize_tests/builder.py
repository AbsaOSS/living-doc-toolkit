# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-tests` builder: a validated documentation input and tests input to a feature-file catalog, each link
with its criterion's state and the release view's links dropped, with no I/O or environment reads.
"""

from collections.abc import Mapping
from datetime import datetime

from living_doc_core.envelope import PRODUCER_NAME, TOOLKIT_VERSION, forwarded
from living_doc_core.views import RELEASE_DROPS
from living_doc_utilities.contracts import doc_source, ui_tests
from living_doc_utilities.contracts.common import LifecycleState, View
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import AuditStats, Cardinality, Metadata, Producer, SourceInputEntry, Stats
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_test_catalog import (
    CatalogAcLink,
    CatalogScenario,
    Document,
    FeatureFileCatalog,
    LinkedScenarios,
    UiTestCatalogResult,
)
from living_doc_utilities.contracts.ui_tests import AcLink, Scenario, UITestsResult


def _feature_file(scenario: Scenario) -> str:
    """Use the qualified path only when two owner/repo parts precede native_id."""
    prefix, separator, _ = scenario.scenario_id.rpartition("/")
    native_id = scenario.source_ref.native_id
    native_id_suffix = f"/{native_id}"
    if not separator or not native_id or not prefix.endswith(native_id_suffix):
        return native_id

    owner_and_repository = prefix[: -len(native_id_suffix)].split("/")
    return prefix if len(owner_and_repository) == 2 and all(owner_and_repository) else native_id


def _entity_ids(scenario: Scenario, prefix: str) -> list[str]:
    """Return each linked entity id once, in first-link order."""
    entity_ids: list[str] = []
    seen: set[str] = set()
    for link in scenario.acceptance_criteria:
        if link.id.startswith(prefix):
            entity_id = link.id.rsplit("-", maxsplit=1)[0]
            if entity_id not in seen:
                seen.add(entity_id)
                entity_ids.append(entity_id)
    return entity_ids


def _criteria_states(documentation: DocSourceResult) -> dict[str, LifecycleState]:
    """The state of every criterion a scenario can link: a User Story's or a Functionality's."""
    return {
        criterion.id: criterion.state
        for entity in (*documentation.user_stories, *documentation.functionalities)
        for criterion in entity.acceptance_criteria
    }


def _kept_links(scenario: Scenario, states: Mapping[str, LifecycleState], view: View) -> list[AcLink]:
    """The links `view` keeps: every one in `inner`; in `release`, none to a `planned` or `in_review` criterion."""
    if view == "inner":
        return list(scenario.acceptance_criteria)
    return [link for link in scenario.acceptance_criteria if states.get(link.id) not in RELEASE_DROPS]


def _catalog_scenario(scenario: Scenario, links: list[AcLink], states: Mapping[str, LifecycleState]) -> CatalogScenario:
    """`scenario` without its file's background, with `links`, each carrying its criterion's state or None."""
    return CatalogScenario(
        **scenario.model_dump(exclude={"background", "acceptance_criteria"}),
        acceptance_criteria=[CatalogAcLink(**link.model_dump(), state=states.get(link.id)) for link in links],
    )


def _place(
    scenario: CatalogScenario, entity_ids: list[str], groups: dict[str, LinkedScenarios], listed: list[LinkedScenarios]
) -> None:
    """Add `scenario` to the group of each of `entity_ids`; a group first met is opened and added to `listed`."""
    for entity_id in entity_ids:
        group = groups.get(entity_id)
        if group is None:
            group = LinkedScenarios(entity_id=entity_id)
            groups[entity_id] = group
            listed.append(group)
        group.scenarios.append(scenario)


def _tests_selection(tests: UITestsResult, states: Mapping[str, LifecycleState], view: View) -> UITestsResult:
    """The tests input with only the links `view` keeps: its stats are the tests entry's `selected_stats`."""
    kept = [
        scenario.model_copy(update={"acceptance_criteria": _kept_links(scenario, states, view)})
        for scenario in tests.scenarios
    ]
    return tests.model_copy(update={"scenarios": kept})


def _source_entry(result: DocSourceResult | UITestsResult, selected: Stats) -> SourceInputEntry:
    return SourceInputEntry(
        schema_version=result.schema_version,
        producer=result.metadata.producer,
        run=result.metadata.run,
        source=result.metadata.source,
        stats=AuditStats.model_validate(result.metadata.stats.model_dump()),
        selected_stats=AuditStats.model_validate(selected.model_dump()),
    )


def build_ui_test_catalog(
    documentation: DocSourceResult, tests: UITestsResult, *, view: View, generated_at: datetime
) -> UiTestCatalogResult:
    """
    Group each scenario by feature file and every User Story or Functionality it links, preserving input order. Each
    link carries its criterion's state from the documentation; the release view drops the links to a `planned` or
    `in_review` criterion, and the scenario stays in the groups its links placed it in.

    @param documentation: The validated documentation input, read for its criteria states only.
    @param tests: The validated tests input, whose scenarios the catalog carries.
    @param view: `document.view`, `inner` or `release`.
    @param generated_at: The write time.
    @return: The output model. Its `metadata.run` is empty, for the caller to set to the CI run. Its `metadata.stats`
        holds only the counts a caller reports, all 0 for a transform, and `write_artifact` computes the rest.
    """
    states = _criteria_states(documentation)
    feature_files: dict[str, FeatureFileCatalog] = {}
    user_story_groups: dict[str, dict[str, LinkedScenarios]] = {}
    functionality_groups: dict[str, dict[str, LinkedScenarios]] = {}

    for scenario in tests.scenarios:
        feature_file = _feature_file(scenario)
        catalog = feature_files.get(feature_file)
        if catalog is None:
            # A feature file's `Background:` is the same on each of its scenarios; it sits on the file once.
            catalog = FeatureFileCatalog(feature_file=feature_file, background=list(scenario.background))
            feature_files[feature_file] = catalog
            user_story_groups[feature_file] = {}
            functionality_groups[feature_file] = {}

        catalog_scenario = _catalog_scenario(scenario, _kept_links(scenario, states, view), states)
        # The groups come from every link the scenario has, so a dropped link never moves it.
        user_story_ids = _entity_ids(scenario, "US-")
        functionality_ids = _entity_ids(scenario, "FUNC-")
        if not user_story_ids and not functionality_ids:
            catalog.unlinked.append(catalog_scenario)
        _place(catalog_scenario, user_story_ids, user_story_groups[feature_file], catalog.linked_to_user_story)
        _place(catalog_scenario, functionality_ids, functionality_groups[feature_file], catalog.linked_to_functionality)

    return UiTestCatalogResult(
        metadata=Metadata(
            producer=Producer(
                name=PRODUCER_NAME,
                version=TOOLKIT_VERSION,
                utilities_version=installed_utilities_version(),
            ),
            source=tests.metadata.source,
            generated_at=generated_at,
            stats=Stats(cardinality=Cardinality()),
            # The documentation is read whole, for every criterion's state; of the tests, the selection is the links
            # the view keeps.
            source_inputs=[
                _source_entry(
                    documentation,
                    compute_stats(documentation, doc_source.RECORD_ROOTS, documentation.metadata.stats.cardinality),
                ),
                _source_entry(
                    tests,
                    compute_stats(
                        _tests_selection(tests, states, view), ui_tests.RECORD_ROOTS, tests.metadata.stats.cardinality
                    ),
                ),
            ],
        ),
        warnings=[
            *(forwarded(warning, documentation.schema_version) for warning in documentation.warnings),
            *(forwarded(warning, tests.schema_version) for warning in tests.warnings),
        ],
        document=Document(view=view),
        feature_files=list(feature_files.values()),
    )
