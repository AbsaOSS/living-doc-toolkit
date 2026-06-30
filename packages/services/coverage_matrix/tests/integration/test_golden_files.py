# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Integration test for the coverage-matrix service using the golden fixtures."""

import json
from pathlib import Path

from living_doc_service_coverage_matrix.service import run_service

FIXTURES = Path(__file__).parent.parent / "fixtures" / "golden"


def test_golden_coverage_matrix(tmp_path):
    """Run the full pipeline and compare against the golden expected output."""
    doc_file = FIXTURES / "doc_source.json"
    tests_file = FIXTURES / "ui_tests.json"
    expected_file = FIXTURES / "expected_coverage_matrix.json"
    out_file = tmp_path / "coverage-matrix.json"

    run_service(str(doc_file), str(tests_file), str(out_file), {})

    with open(expected_file, "r", encoding="utf-8") as f:
        expected = json.load(f)
    with open(out_file, "r", encoding="utf-8") as f:
        actual = json.load(f)

    # generated_at is dynamic; normalise before comparing.
    assert actual["generated_at"]
    actual["generated_at"] = "PLACEHOLDER"

    assert actual == expected, "Output does not match the golden expected_coverage_matrix.json"


def test_golden_summary_and_buckets(tmp_path):
    """Assert the key coverage facts produced from the golden fixtures."""
    doc_file = FIXTURES / "doc_source.json"
    tests_file = FIXTURES / "ui_tests.json"
    out_file = tmp_path / "coverage-matrix.json"

    matrix = run_service(str(doc_file), str(tests_file), str(out_file), {})

    summary = matrix.summary
    assert summary.total_user_stories == 3
    assert summary.total_acs == 5
    assert summary.active_acs == 4
    assert summary.covered_acs == 3
    assert summary.coverage_pct == 75.0

    us_by_id = {us.id: us for us in matrix.user_stories}

    # US-1: the deprecated AC is covered but excluded from coverage_pct.
    us1 = us_by_id["US-1"]
    us1_cov = {ac.id: ac.coverage for ac in us1.acceptance_criteria}
    assert us1_cov["US-1-01"].status == "covered"
    assert us1_cov["US-1-01"].test_count == 2
    assert us1_cov["US-1-02"].status == "covered"
    assert us1_cov["US-1-03"].status == "covered"
    assert us1.summary.coverage_pct == 100.0

    # US-2: one covered, one not covered.
    us2 = us_by_id["US-2"]
    us2_cov = {ac.id: ac.coverage.status for ac in us2.acceptance_criteria}
    assert us2_cov == {"US-2-01": "covered", "US-2-02": "not_covered"}

    # US-7: no ACs -> null coverage_pct.
    us7 = us_by_id["US-7"]
    assert us7.acceptance_criteria == []
    assert us7.summary.coverage_pct is None

    # Two unlinked scenarios (null us_id and unresolved US-99) and one stale AC ref.
    unlinked_us_ids = sorted(str(t.us_id) for t in matrix.unlinked_tests)
    assert unlinked_us_ids == ["None", "US-99"]
    assert len(matrix.stale_ac_refs) == 1
    assert matrix.stale_ac_refs[0].stale_ac_id == "US-1-99"
    assert matrix.stale_ac_refs[0].us_id == "US-1"

