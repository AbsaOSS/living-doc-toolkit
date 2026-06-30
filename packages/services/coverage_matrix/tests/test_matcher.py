# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the matcher module."""

from living_doc_service_coverage_matrix.matcher import build_coverage_matrix

GENERATED_AT = "2026-06-30T00:00:00+00:00"


def _us(num, acs, state="active", title="Title"):
    return {
        "id": f"org/repo/{num}",
        "title": title,
        "state": state,
        "acceptance_criteria": acs,
    }


def _ac(ac_id, state="Active", version="v1.0.0", description="desc"):
    return {"id": ac_id, "state": state, "version": version, "description": description}


def _scenario(scenario_id, us_id, ac_ids, name="scenario", tags=None, source=None):
    return {
        "id": scenario_id,
        "us_id": us_id,
        "ac_ids": ac_ids,
        "scenario_name": name,
        "tags": tags if tags is not None else ["Regression"],
        "source": source if source is not None else {"org": "org", "repo": "repo", "file": "f.feature"},
    }


def test_covered_and_not_covered():
    doc = [_us("US-1", [_ac("US-1-01"), _ac("US-1-02")])]
    tests = [_scenario("s1", "US-1", ["US-1-01"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    us = matrix.user_stories[0]
    assert us.id == "US-1"
    assert us.full_id == "org/repo/US-1"
    ac1, ac2 = us.acceptance_criteria
    assert ac1.coverage.status == "covered"
    assert ac1.coverage.test_count == 1
    assert ac1.coverage.tests[0].id == "s1"
    assert ac2.coverage.status == "not_covered"
    assert ac2.coverage.test_count == 0
    assert ac2.coverage.tests == []


def test_us_summary_counts():
    doc = [_us("US-1", [_ac("US-1-01"), _ac("US-1-02")])]
    tests = [_scenario("s1", "US-1", ["US-1-01"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    summary = matrix.user_stories[0].summary
    assert summary.total_acs == 2
    assert summary.active_acs == 2
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 50.0


def test_deprecated_ac_excluded_from_pct():
    doc = [_us("US-1", [_ac("US-1-01"), _ac("US-1-02", state="Deprecated")])]
    tests = [_scenario("s1", "US-1", ["US-1-01", "US-1-02"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    summary = matrix.user_stories[0].summary
    assert summary.total_acs == 2
    assert summary.active_acs == 1
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 100.0


def test_unlinked_when_us_id_null():
    doc = [_us("US-1", [_ac("US-1-01")])]
    tests = [_scenario("s1", None, ["US-1-01"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    assert matrix.user_stories[0].acceptance_criteria[0].coverage.status == "not_covered"
    assert len(matrix.unlinked_tests) == 1
    assert matrix.unlinked_tests[0].id == "s1"
    assert matrix.unlinked_tests[0].us_id is None


def test_unlinked_when_us_id_unresolved():
    doc = [_us("US-1", [_ac("US-1-01")])]
    tests = [_scenario("s1", "US-99", ["US-99-01"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    assert len(matrix.unlinked_tests) == 1
    assert matrix.unlinked_tests[0].us_id == "US-99"
    assert matrix.stale_ac_refs == []


def test_stale_ac_ref_recorded():
    doc = [_us("US-1", [_ac("US-1-01")])]
    tests = [_scenario("s1", "US-1", ["US-1-01", "US-1-99"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    assert matrix.user_stories[0].acceptance_criteria[0].coverage.status == "covered"
    assert len(matrix.stale_ac_refs) == 1
    stale = matrix.stale_ac_refs[0]
    assert stale.scenario_id == "s1"
    assert stale.us_id == "US-1"
    assert stale.stale_ac_id == "US-1-99"


def test_multiple_tests_for_one_ac():
    doc = [_us("US-1", [_ac("US-1-01")])]
    tests = [
        _scenario("s1", "US-1", ["US-1-01"]),
        _scenario("s2", "US-1", ["US-1-01"]),
    ]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    coverage = matrix.user_stories[0].acceptance_criteria[0].coverage
    assert coverage.test_count == 2
    assert {t.id for t in coverage.tests} == {"s1", "s2"}


def test_top_summary_aggregation():
    doc = [
        _us("US-1", [_ac("US-1-01"), _ac("US-1-02")]),
        _us("US-2", [_ac("US-2-01")]),
    ]
    tests = [_scenario("s1", "US-1", ["US-1-01"])]

    matrix = build_coverage_matrix(doc, tests, GENERATED_AT)

    summary = matrix.summary
    assert summary.total_user_stories == 2
    assert summary.total_acs == 3
    assert summary.active_acs == 3
    assert summary.covered_acs == 1
    assert summary.coverage_pct == 33.3


def test_coverage_pct_null_when_no_active_acs():
    doc = [_us("US-1", [_ac("US-1-01", state="Deprecated")])]

    matrix = build_coverage_matrix(doc, [], GENERATED_AT)

    assert matrix.summary.coverage_pct is None
    assert matrix.user_stories[0].summary.coverage_pct is None


def test_schema_version_and_timestamp():
    matrix = build_coverage_matrix([], [], GENERATED_AT)

    assert matrix.schema_version == "coverage-matrix-v1.0.0"
    assert matrix.generated_at == GENERATED_AT
    assert matrix.summary.total_user_stories == 0
