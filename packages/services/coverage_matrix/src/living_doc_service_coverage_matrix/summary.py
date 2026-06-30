# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Summary computation for the coverage matrix.

Pure functions that tally AC coverage. An AC contributes to ``covered_acs`` only when
it is Active and covered, so deprecated ACs never inflate ``coverage_pct``.
"""

from living_doc_service_coverage_matrix.model.coverage_item import (
    AcCoverage,
    Summary,
    TopSummary,
    UserStoryCoverage,
)

ACTIVE_STATE = "Active"
COVERED = "covered"


def _coverage_pct(covered: int, active: int) -> float | None:
    """Return covered/active as a percentage rounded to 1 dp, or None when active is 0."""
    if active == 0:
        return None
    return round(covered / active * 100, 1)


def _is_active_covered(ac: AcCoverage) -> bool:
    """True when an AC is Active and has at least one covering test."""
    return ac.state == ACTIVE_STATE and ac.coverage.status == COVERED


def compute_us_summary(acceptance_criteria: list[AcCoverage]) -> Summary:
    """Compute the coverage summary for a single User Story's acceptance criteria."""
    total = len(acceptance_criteria)
    active = sum(1 for ac in acceptance_criteria if ac.state == ACTIVE_STATE)
    covered = sum(1 for ac in acceptance_criteria if _is_active_covered(ac))
    return Summary(
        total_acs=total,
        active_acs=active,
        covered_acs=covered,
        coverage_pct=_coverage_pct(covered, active),
    )


def compute_summary(user_stories: list[UserStoryCoverage]) -> TopSummary:
    """Compute the top-level coverage summary across all User Stories."""
    all_acs = [ac for us in user_stories for ac in us.acceptance_criteria]
    total = len(all_acs)
    active = sum(1 for ac in all_acs if ac.state == ACTIVE_STATE)
    covered = sum(1 for ac in all_acs if _is_active_covered(ac))
    return TopSummary(
        total_user_stories=len(user_stories),
        total_acs=total,
        active_acs=active,
        covered_acs=covered,
        coverage_pct=_coverage_pct(covered, active),
    )
