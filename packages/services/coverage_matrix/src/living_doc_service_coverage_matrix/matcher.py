# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Coverage matcher.

Pure transformation: takes parsed doc groups (user stories, functionalities, features)
and test scenarios and returns a :class:`CoverageMatrix`. No file I/O and no logging —
fully unit-testable.
"""

from collections import defaultdict

from living_doc_service_coverage_matrix.model.coverage_item import (
    AcCoverage,
    Coverage,
    CoverageMatrix,
    FeatureEntry,
    FunctionalityCoverage,
    StaleAcRef,
    TestRef,
    UnlinkedTest,
    UserStoryCoverage,
)
from living_doc_service_coverage_matrix.summary import compute_summary, compute_us_summary

SCHEMA_VERSION = "coverage-matrix-v1.0.0"
COVERED = "covered"
NOT_COVERED = "not_covered"


def _short_id(full_id: str) -> str:
    """Extract the short id (e.g. ``US-27`` / ``FUNC-001``) from ``org/repo/US-27``."""
    return full_id.split("/")[-1]


def _test_ref(scenario: dict) -> TestRef:
    """Build a TestRef from a scenario dictionary."""
    return TestRef(
        id=scenario.get("id"),
        scenario_name=scenario.get("scenario_name"),
        tags=scenario.get("tags") or [],
        source=scenario.get("source"),
    )


def _ac_ids_of(entity: dict) -> set[str]:
    """Collect the set of AC ids declared on an entity."""
    return {ac.get("id") for ac in entity.get("acceptance_criteria") or []}


def _resolve_tests(
    test_items: list[dict],
    us_by_num: dict[str, dict],
    func_by_num: dict[str, dict],
) -> tuple[
    dict[str, dict[str, list[TestRef]]],
    dict[str, dict[str, list[TestRef]]],
    list[UnlinkedTest],
    list[StaleAcRef],
]:
    """Split scenarios into per-US and per-Functionality coverage maps, unlinked, and stale refs."""
    us_map: dict[str, dict[str, list[TestRef]]] = defaultdict(lambda: defaultdict(list))
    func_map: dict[str, dict[str, list[TestRef]]] = defaultdict(lambda: defaultdict(list))
    unlinked: list[UnlinkedTest] = []
    stale: list[StaleAcRef] = []

    for scenario in test_items:
        us_id = scenario.get("us_id")
        func_id = scenario.get("func_id")
        us = us_by_num.get(us_id) if us_id else None
        func = func_by_num.get(func_id) if func_id else None

        if us is None and func is None:
            unlinked.append(
                UnlinkedTest(
                    id=scenario.get("id"),
                    scenario_name=scenario.get("scenario_name"),
                    us_id=us_id,
                    func_id=func_id,
                    ac_ids=scenario.get("ac_ids") or [],
                    source=scenario.get("source"),
                )
            )
            continue

        us_ac_ids = _ac_ids_of(us) if us is not None else set()
        func_ac_ids = _ac_ids_of(func) if func is not None else set()
        us_key = _short_id(us["id"]) if us is not None else None
        func_key = _short_id(func["id"]) if func is not None else None

        for ac_id in scenario.get("ac_ids") or []:
            matched = False
            if us_key is not None and ac_id in us_ac_ids:
                us_map[us_key][ac_id].append(_test_ref(scenario))
                matched = True
            if func_key is not None and ac_id in func_ac_ids:
                func_map[func_key][ac_id].append(_test_ref(scenario))
                matched = True
            if not matched:
                stale.append(
                    StaleAcRef(
                        scenario_id=scenario.get("id"),
                        scenario_name=scenario.get("scenario_name"),
                        us_id=us_id,
                        func_id=func_id,
                        stale_ac_id=ac_id,
                        source=scenario.get("source"),
                    )
                )

    return us_map, func_map, unlinked, stale


def _build_ac_coverages(entity: dict, ac_tests: dict[str, list[TestRef]]) -> list[AcCoverage]:
    """Build the per-AC coverage list for an entity."""
    ac_coverages: list[AcCoverage] = []
    for ac in entity.get("acceptance_criteria") or []:
        tests = ac_tests.get(ac.get("id"), [])
        status = COVERED if tests else NOT_COVERED
        ac_coverages.append(
            AcCoverage(
                id=ac.get("id"),
                state=ac.get("state"),
                version=ac.get("version"),
                description=ac.get("description"),
                coverage=Coverage(status=status, test_count=len(tests), tests=tests),
            )
        )
    return ac_coverages


def _build_user_story(us: dict, ac_tests: dict[str, list[TestRef]]) -> UserStoryCoverage:
    """Build a single UserStoryCoverage from a US dict and its resolved AC tests."""
    ac_coverages = _build_ac_coverages(us, ac_tests)
    return UserStoryCoverage(
        id=_short_id(us["id"]),
        full_id=us["id"],
        title=us.get("title"),
        state=us.get("state"),
        summary=compute_us_summary(ac_coverages),
        acceptance_criteria=ac_coverages,
    )


def _build_functionality(func: dict, ac_tests: dict[str, list[TestRef]]) -> FunctionalityCoverage:
    """Build a single FunctionalityCoverage from a functionality dict and its resolved AC tests."""
    ac_coverages = _build_ac_coverages(func, ac_tests)
    return FunctionalityCoverage(
        id=_short_id(func["id"]),
        full_id=func["id"],
        title=func.get("title"),
        state=func.get("state"),
        parent=func.get("parent"),
        func_type=func.get("func_type"),
        summary=compute_us_summary(ac_coverages),
        acceptance_criteria=ac_coverages,
    )


def _build_feature(feature: dict) -> FeatureEntry:
    """Build a single FeatureEntry from a feature dict (registry surface, no ACs)."""
    return FeatureEntry(
        id=_short_id(feature["id"]),
        full_id=feature["id"],
        title=feature.get("title"),
        state=feature.get("state"),
        surface_type=feature.get("surface_type"),
        route=feature.get("route"),
        owners=feature.get("owners"),
        purpose=feature.get("purpose"),
        user_stories=feature.get("user_stories") or [],
        functionalities=feature.get("functionalities") or [],
        external_dependencies=feature.get("external_dependencies"),
        page_object=feature.get("page_object"),
    )


def build_coverage_matrix(doc: dict, test_items: list[dict], generated_at: str) -> CoverageMatrix:
    """
    Cross-reference User Stories, Functionalities, Features and UI tests into a coverage matrix.

    Args:
        doc: Doc groups with ``user_stories``, ``functionalities`` and ``features`` lists
        test_items: UI test scenario dictionaries
        generated_at: ISO-8601 timestamp recorded on the matrix

    Returns:
        A fully populated :class:`CoverageMatrix`.
    """
    doc_us = doc.get("user_stories") or []
    doc_func = doc.get("functionalities") or []
    doc_feat = doc.get("features") or []

    us_by_num = {_short_id(us["id"]): us for us in doc_us}
    func_by_num = {_short_id(func["id"]): func for func in doc_func}

    us_map, func_map, unlinked, stale = _resolve_tests(test_items, us_by_num, func_by_num)

    user_stories = [_build_user_story(us, us_map.get(_short_id(us["id"]), {})) for us in doc_us]
    functionalities = [_build_functionality(func, func_map.get(_short_id(func["id"]), {})) for func in doc_func]
    features = [_build_feature(feature) for feature in doc_feat]

    return CoverageMatrix(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        summary=compute_summary(user_stories, functionalities, len(features)),
        user_stories=user_stories,
        functionalities=functionalities,
        features=features,
        unlinked_tests=unlinked,
        stale_ac_refs=stale,
    )
