# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Dataclasses for the coverage-matrix output document.

These types mirror ``coverage-matrix-v1.0.0-schema.json`` and serialize to plain
dictionaries via :meth:`CoverageMatrix.to_dict`.
"""

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class Summary:
    """AC coverage tallies scoped to a single User Story."""

    total_acs: int
    active_acs: int
    covered_acs: int
    coverage_pct: Optional[float]


@dataclass
class TopSummary:
    """AC coverage tallies aggregated across all User Stories."""

    total_user_stories: int
    total_acs: int
    active_acs: int
    covered_acs: int
    coverage_pct: Optional[float]


@dataclass
class TestRef:
    """A reference to a UI test scenario covering an acceptance criterion."""

    id: Optional[str]
    scenario_name: Optional[str]
    tags: list[str]
    source: Optional[dict[str, Any]]


@dataclass
class Coverage:
    """Coverage status and linked tests for a single acceptance criterion."""

    status: str
    test_count: int
    tests: list[TestRef]


@dataclass
class AcCoverage:
    """An acceptance criterion with its resolved coverage."""

    id: Optional[str]
    state: Optional[str]
    version: Optional[str]
    description: Optional[str]
    coverage: Coverage


@dataclass
class UserStoryCoverage:
    """A User Story with per-AC coverage and a scoped summary."""

    id: str
    full_id: str
    title: Optional[str]
    state: Optional[str]
    summary: Summary
    acceptance_criteria: list[AcCoverage]


@dataclass
class UnlinkedTest:
    """A scenario whose ``us_id`` is null or does not resolve to a known US."""

    id: Optional[str]
    scenario_name: Optional[str]
    us_id: Optional[str]
    ac_ids: list[str]
    source: Optional[dict[str, Any]]


@dataclass
class StaleAcRef:
    """An ``ac_id`` referenced by a scenario that does not exist on the resolved US."""

    scenario_id: Optional[str]
    scenario_name: Optional[str]
    us_id: Optional[str]
    stale_ac_id: str
    source: Optional[dict[str, Any]]


@dataclass
class CoverageMatrix:
    """Top-level coverage-matrix document."""

    schema_version: str
    generated_at: str
    summary: TopSummary
    user_stories: list[UserStoryCoverage]
    unlinked_tests: list[UnlinkedTest]
    stale_ac_refs: list[StaleAcRef]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the matrix to a plain dictionary suitable for JSON output."""
        return asdict(self)
