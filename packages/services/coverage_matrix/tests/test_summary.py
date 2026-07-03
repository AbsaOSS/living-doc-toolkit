# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the summary module."""

from living_doc_service_coverage_matrix.model.coverage_item import (
    AcCoverage,
    Coverage,
    FunctionalityCoverage,
    UserStoryCoverage,
)
from living_doc_service_coverage_matrix.summary import compute_summary, compute_us_summary


def _ac(state, status):
    return AcCoverage(
        id="US-1-01",
        state=state,
        version="v1.0.0",
        description="desc",
        coverage=Coverage(status=status, test_count=1 if status == "covered" else 0, tests=[]),
    )


def test_compute_us_summary_mixed():
    acs = [
        _ac("Active", "covered"),
        _ac("Active", "not_covered"),
        _ac("Deprecated", "covered"),
    ]

    summary = compute_us_summary(acs)

    assert summary.total_acs == 3
    assert summary.active_acs == 2
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 50.0


def test_compute_us_summary_empty():
    summary = compute_us_summary([])

    assert summary.total_acs == 0
    assert summary.active_acs == 0
    assert summary.covered_acs == 0
    assert summary.coverage_pct is None


def test_compute_summary_aggregates_user_stories():
    us1 = UserStoryCoverage(
        id="US-1",
        full_id="org/repo/US-1",
        title="t",
        state="active",
        summary=compute_us_summary([_ac("Active", "covered")]),
        acceptance_criteria=[_ac("Active", "covered")],
    )
    us2 = UserStoryCoverage(
        id="US-2",
        full_id="org/repo/US-2",
        title="t",
        state="active",
        summary=compute_us_summary([_ac("Active", "not_covered")]),
        acceptance_criteria=[_ac("Active", "not_covered")],
    )

    summary = compute_summary([us1, us2], [], 0)

    assert summary.total_user_stories == 2
    assert summary.total_functionalities == 0
    assert summary.total_features == 0
    assert summary.total_acs == 2
    assert summary.active_acs == 2
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 50.0


def test_compute_summary_aggregates_functionalities():
    us = UserStoryCoverage(
        id="US-1",
        full_id="org/repo/US-1",
        title="t",
        state="active",
        summary=compute_us_summary([_ac("Active", "covered")]),
        acceptance_criteria=[_ac("Active", "covered")],
    )
    func = FunctionalityCoverage(
        id="FUNC-001",
        full_id="org/repo/FUNC-001",
        title="t",
        state="active",
        parent="org/repo/US-1",
        func_type="unit",
        summary=compute_us_summary([_ac("Active", "not_covered")]),
        acceptance_criteria=[_ac("Active", "not_covered")],
    )

    summary = compute_summary([us], [func], 3)

    assert summary.total_user_stories == 1
    assert summary.total_functionalities == 1
    assert summary.total_features == 3
    assert summary.total_acs == 2
    assert summary.active_acs == 2
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 50.0
