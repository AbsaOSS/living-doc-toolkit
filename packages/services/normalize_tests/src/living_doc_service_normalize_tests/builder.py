# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The `normalize-tests` builder: validated UI tests to a feature-file catalog, with no I/O or environment reads."""

from datetime import datetime

from living_doc_core.envelope import PRODUCER_NAME, TOOLKIT_VERSION, forwarded
from living_doc_utilities.contracts import ui_tests
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.envelope import AuditStats, Cardinality, Metadata, Producer, SourceInputEntry, Stats
from living_doc_utilities.contracts.stats import compute_stats
from living_doc_utilities.contracts.ui_test_catalog import (
    Document,
    FeatureFileCatalog,
    LinkedScenarios,
    UiTestCatalogResult,
)
from living_doc_utilities.contracts.ui_tests import Scenario, UITestsResult


def _feature_file(scenario: Scenario) -> str:
    """Use the collector id's repository-qualified file path when it matches native_id; otherwise use native_id."""
    prefix, separator, _ = scenario.scenario_id.rpartition("/")
    native_id = scenario.source_ref.native_id
    return prefix if separator and prefix.endswith(f"/{native_id}") else native_id


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


def build_ui_test_catalog(tests: UITestsResult, *, generated_at: datetime) -> UiTestCatalogResult:
    """Group each scenario by feature file and every linked User Story or Functionality, preserving input order."""
    feature_files: dict[str, FeatureFileCatalog] = {}
    user_story_groups: dict[str, dict[str, LinkedScenarios]] = {}
    functionality_groups: dict[str, dict[str, LinkedScenarios]] = {}

    for scenario in tests.scenarios:
        feature_file = _feature_file(scenario)
        catalog = feature_files.get(feature_file)
        if catalog is None:
            catalog = FeatureFileCatalog(feature_file=feature_file)
            feature_files[feature_file] = catalog
            user_story_groups[feature_file] = {}
            functionality_groups[feature_file] = {}

        user_story_ids = _entity_ids(scenario, "US-")
        functionality_ids = _entity_ids(scenario, "FUNC-")
        if not user_story_ids and not functionality_ids:
            catalog.unlinked.append(scenario)

        for entity_id in user_story_ids:
            group = user_story_groups[feature_file].get(entity_id)
            if group is None:
                group = LinkedScenarios(entity_id=entity_id)
                user_story_groups[feature_file][entity_id] = group
                catalog.linked_to_user_story.append(group)
            group.scenarios.append(scenario)

        for entity_id in functionality_ids:
            group = functionality_groups[feature_file].get(entity_id)
            if group is None:
                group = LinkedScenarios(entity_id=entity_id)
                functionality_groups[feature_file][entity_id] = group
                catalog.linked_to_functionality.append(group)
            group.scenarios.append(scenario)

    selected_stats = compute_stats(tests, ui_tests.RECORD_ROOTS, tests.metadata.stats.cardinality)
    source = tests.metadata.source
    return UiTestCatalogResult(
        metadata=Metadata(
            producer=Producer(
                name=PRODUCER_NAME,
                version=TOOLKIT_VERSION,
                utilities_version=installed_utilities_version(),
            ),
            source=source,
            generated_at=generated_at,
            stats=Stats(cardinality=Cardinality()),
            source_inputs=[
                SourceInputEntry(
                    schema_version=tests.schema_version,
                    producer=tests.metadata.producer,
                    run=tests.metadata.run,
                    source=source,
                    stats=AuditStats.model_validate(tests.metadata.stats.model_dump()),
                    selected_stats=AuditStats.model_validate(selected_stats.model_dump()),
                )
            ],
        ),
        warnings=[forwarded(warning, tests.schema_version) for warning in tests.warnings],
        document=Document(view="inner"),
        feature_files=list(feature_files.values()),
    )
