# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Coverage matcher.

Pure transformation: takes parsed doc and tests item lists and returns a
:class:`CoverageMatrix`. No file I/O and no logging — fully unit-testable.
"""

from collections import defaultdict

from living_doc_service_coverage_matrix.model.coverage_item import (
    AcCoverage,
    Coverage,
    CoverageMatrix,
    StaleAcRef,
    TestRef,
    UnlinkedTest,
    UserStoryCoverage,
)
from living_doc_service_coverage_matrix.summary import compute_summary, compute_us_summary

SCHEMA_VERSION = "coverage-matrix-v1.0.0"
COVERED = "covered"
NOT_COVERED = "not_covered"


def _us_num(full_id: str) -> str:
    """Extract the short US id (e.g. ``US-27``) from a full id like ``org/repo/US-27``."""
    return full_id.split("/")[-1]


def _test_ref(scenario: dict) -> TestRef:
    """Build a TestRef from a scenario dictionary."""
    return TestRef(
        id=scenario.get("id"),
        scenario_name=scenario.get("scenario_name"),
        tags=scenario.get("tags") or [],
        source=scenario.get("source"),
    )


def _resolve_tests(
    test_items: list[dict],
    us_by_num: dict[str, dict],
) -> tuple[dict[str, dict[str, list[TestRef]]], list[UnlinkedTest], list[StaleAcRef]]:
    """Split scenarios into a per-US coverage map, unlinked tests, and stale AC refs."""
    coverage_map: dict[str, dict[str, list[TestRef]]] = defaultdict(lambda: defaultdict(list))
    unlinked: list[UnlinkedTest] = []
    stale: list[StaleAcRef] = []

    for scenario in test_items:
        us_id = scenario.get("us_id")
        if not us_id or us_id not in us_by_num:
            unlinked.append(
                UnlinkedTest(
                    id=scenario.get("id"),
                    scenario_name=scenario.get("scenario_name"),
                    us_id=us_id,
                    ac_ids=scenario.get("ac_ids") or [],
                    source=scenario.get("source"),
                )
            )
            continue

        valid_ac_ids = {ac.get("id") for ac in us_by_num[us_id]["acceptance_criteria"]}
        for ac_id in scenario.get("ac_ids") or []:
            if ac_id in valid_ac_ids:
                coverage_map[us_id][ac_id].append(_test_ref(scenario))
            else:
                stale.append(
                    StaleAcRef(
                        scenario_id=scenario.get("id"),
                        scenario_name=scenario.get("scenario_name"),
                        us_id=us_id,
                        stale_ac_id=ac_id,
                        source=scenario.get("source"),
                    )
                )

    return coverage_map, unlinked, stale


def _build_user_story(us: dict, ac_tests: dict[str, list[TestRef]]) -> UserStoryCoverage:
    """Build a single UserStoryCoverage from a US dict and its resolved AC tests."""
    ac_coverages: list[AcCoverage] = []
    for ac in us["acceptance_criteria"]:
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
    return UserStoryCoverage(
        id=_us_num(us["id"]),
        full_id=us["id"],
        title=us.get("title"),
        state=us.get("state"),
        summary=compute_us_summary(ac_coverages),
        acceptance_criteria=ac_coverages,
    )


def build_coverage_matrix(doc_items: list[dict], test_items: list[dict], generated_at: str) -> CoverageMatrix:
    """
    Cross-reference User Stories and UI tests into a coverage matrix.

    Args:
        doc_items: User Story dictionaries (each with ``id`` and ``acceptance_criteria``)
        test_items: UI test scenario dictionaries
        generated_at: ISO-8601 timestamp recorded on the matrix

    Returns:
        A fully populated :class:`CoverageMatrix`.
    """
    us_by_num = {_us_num(us["id"]): us for us in doc_items}
    coverage_map, unlinked, stale = _resolve_tests(test_items, us_by_num)

    user_stories = [_build_user_story(us, coverage_map.get(_us_num(us["id"]), {})) for us in doc_items]

    return CoverageMatrix(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        summary=compute_summary(user_stories),
        user_stories=user_stories,
        unlinked_tests=unlinked,
        stale_ac_refs=stale,
    )
