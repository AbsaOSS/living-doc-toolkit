# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Integration tests for the coverage-matrix service.

The ``golden/`` fixtures are **real** ``living-doc-collector-gh`` output: the ``.feature``
corpus in ``tests/fixtures/corpus/`` is mined by the collector's ``doc-source`` and
``ui-tests`` modes via ``tests/fixtures/generate_golden_inputs.py`` (the exact collector
commit is recorded in ``golden/collector_provenance.json``), and the expected coverage
matrix is regenerated with
``tests/fixtures/golden/regenerate_expected.py``. Refreshing the golden inputs is a
two-step manual process documented in ``tests/fixtures/README.md``.

The ``synthetic/`` fixtures are hand-authored and cover shapes the corpus does not
produce naturally (empty inputs, a cross-source ``US-1`` id collision, an unmatched AC).
"""

import json
import re
from pathlib import Path

from living_doc_service_coverage_matrix.service import run_service

FIXTURES = Path(__file__).parent.parent / "fixtures"
GOLDEN = FIXTURES / "golden"
SYNTHETIC = FIXTURES / "synthetic"


def test_golden_coverage_matrix(tmp_path):
    """Run the full pipeline and compare against the golden expected output."""
    out_file = tmp_path / "coverage-matrix.json"

    run_service(str(GOLDEN / "doc_source.json"), str(GOLDEN / "ui_tests.json"), str(out_file), {})

    expected = json.loads((GOLDEN / "expected_coverage_matrix.json").read_text(encoding="utf-8"))
    actual = json.loads(out_file.read_text(encoding="utf-8"))

    # generated_at is dynamic; normalise before comparing.
    assert actual["generated_at"]
    actual["generated_at"] = "PLACEHOLDER"

    assert actual == expected, "Output does not match the golden expected_coverage_matrix.json"


def test_golden_inputs_are_real_collector_output():
    """Guard that the golden inputs are collector-gh output, not hand-authored JSON."""
    doc = json.loads((GOLDEN / "doc_source.json").read_text(encoding="utf-8"))
    tests = json.loads((GOLDEN / "ui_tests.json").read_text(encoding="utf-8"))

    for payload in (doc, tests):
        assert payload["metadata"]["producer"]["name"] == "AbsaOSS/living-doc-collector-gh"

    # Provenance: generate_golden_inputs.py records the exact collector-gh commit it mined.
    provenance = json.loads((GOLDEN / "collector_provenance.json").read_text(encoding="utf-8"))
    assert re.fullmatch(r"[0-9a-f]{40}", provenance["collector_gh_commit"])

    # doc-source keeps the three named lists; ui-tests uses a flat items[] array.
    assert set(doc) >= {"user_stories", "functionalities", "features"}
    assert isinstance(tests["items"], list)

    # The AC-ID join key: every scenario ac_id resolves to a real AC or is a known stale ref.
    declared_ac_ids = {ac["id"] for us in doc["user_stories"] for ac in us["acceptance_criteria"]}
    assert {"US-1-01", "US-1-02", "US-1-03", "US-2-01", "US-2-02"} == declared_ac_ids
    scenario_ac_ids = {ac_id for item in tests["items"] for ac_id in item["ac_ids"]}
    assert {"US-1-01", "US-1-02", "US-1-03"} <= scenario_ac_ids
    assert "US-1-99" in scenario_ac_ids  # the intentional stale ref


def test_golden_summary_and_buckets(tmp_path):
    """Assert the key coverage facts produced from the golden fixtures."""
    out_file = tmp_path / "coverage-matrix.json"
    matrix = run_service(str(GOLDEN / "doc_source.json"), str(GOLDEN / "ui_tests.json"), str(out_file), {})

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
    assert us1_cov["US-1-01"].test_count == 1
    assert us1_cov["US-1-02"].status == "covered"
    assert us1_cov["US-1-02"].test_count == 2  # positive (valid login) + negative (disabled button)
    assert us1_cov["US-1-03"].status == "covered"
    assert us1.acceptance_criteria[2].state == "Deprecated"
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


def test_synthetic_empty_inputs(tmp_path):
    """Empty doc-source / ui-tests inputs produce an empty matrix, not an error."""
    out_file = tmp_path / "coverage-matrix.json"
    matrix = run_service(
        str(SYNTHETIC / "empty_doc_source.json"), str(SYNTHETIC / "empty_ui_tests.json"), str(out_file), {}
    )

    assert matrix.summary.total_user_stories == 0
    assert matrix.summary.total_acs == 0
    assert matrix.summary.coverage_pct is None
    assert matrix.user_stories == []
    assert matrix.unlinked_tests == []
    assert matrix.stale_ac_refs == []


def test_synthetic_cross_source_collision(tmp_path):
    """
    Two User Stories share the short id ``US-1`` across sources. The matcher disambiguates
    on the scenario ``source`` org/repo, so a scenario from ``absa-group/aul-ui`` covers
    that US-1's AC and does not leak onto the ``other-org`` US-1.
    """
    out_file = tmp_path / "coverage-matrix.json"
    matrix = run_service(
        str(SYNTHETIC / "collision_doc_source.json"), str(SYNTHETIC / "collision_ui_tests.json"), str(out_file), {}
    )

    us_by_full = {us.full_id: us for us in matrix.user_stories}
    assert list(us_by_full) == ["absa-group/aul-ui/US-1", "other-org/other-repo/US-1"]

    # The absa-group scenario resolves to the absa-group US-1: its AC is covered.
    absa = {ac.id: ac.coverage.status for ac in us_by_full["absa-group/aul-ui/US-1"].acceptance_criteria}
    assert absa == {"US-1-01": "covered"}
    # The other-org US-1 has no scenario of its own -> its AC stays uncovered.
    other = {ac.id: ac.coverage.status for ac in us_by_full["other-org/other-repo/US-1"].acceptance_criteria}
    assert other == {"US-1-02": "not_covered"}

    # Only the genuinely nonexistent AC id is stale; the US-5 scenario is unlinked.
    stale_ids = sorted(ref.stale_ac_id for ref in matrix.stale_ac_refs)
    assert stale_ids == ["US-1-77"]
    assert [t.us_id for t in matrix.unlinked_tests] == ["US-5"]
