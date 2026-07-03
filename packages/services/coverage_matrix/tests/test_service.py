# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the service orchestration module."""

import json

import pytest

from living_doc_service_coverage_matrix.service import CoverageThresholdError, run_service


def _write(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _doc_payload():
    return {
        "items": [
            {
                "id": "org/repo/US-1",
                "title": "User Login",
                "state": "active",
                "acceptance_criteria": [
                    {"id": "US-1-01", "state": "Active", "version": "v1.0.0", "description": "a"},
                    {"id": "US-1-02", "state": "Active", "version": "v1.0.0", "description": "b"},
                ],
            }
        ]
    }


def _tests_payload():
    return {
        "items": [
            {
                "id": "s1",
                "us_id": "US-1",
                "ac_ids": ["US-1-01"],
                "scenario_name": "scenario one",
                "tags": ["Regression"],
                "source": {"org": "org", "repo": "repo", "file": "f.feature"},
            }
        ]
    }


def test_run_service_writes_output(tmp_path):
    doc_file = tmp_path / "doc.json"
    tests_file = tmp_path / "tests.json"
    out_file = tmp_path / "coverage-matrix.json"
    _write(doc_file, _doc_payload())
    _write(tests_file, _tests_payload())

    run_service(str(doc_file), str(tests_file), str(out_file), {})

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema_version"] == "coverage-matrix-v1.0.0"
    assert data["summary"]["total_user_stories"] == 1
    assert data["summary"]["covered_acs"] == 1
    assert data["summary"]["coverage_pct"] == 50.0
    assert data["user_stories"][0]["id"] == "US-1"


def test_run_service_skips_invalid_user_story(tmp_path):
    doc_file = tmp_path / "doc.json"
    tests_file = tmp_path / "tests.json"
    out_file = tmp_path / "out.json"
    payload = _doc_payload()
    payload["items"].append({"title": "no id"})
    payload["items"].append({"id": "org/repo/US-2"})  # missing acceptance_criteria
    _write(doc_file, payload)
    _write(tests_file, _tests_payload())

    matrix = run_service(str(doc_file), str(tests_file), str(out_file), {})

    assert matrix.summary.total_user_stories == 1


def test_run_service_fail_under_raises(tmp_path):
    doc_file = tmp_path / "doc.json"
    tests_file = tmp_path / "tests.json"
    out_file = tmp_path / "out.json"
    _write(doc_file, _doc_payload())
    _write(tests_file, _tests_payload())

    with pytest.raises(CoverageThresholdError):
        run_service(str(doc_file), str(tests_file), str(out_file), {"fail_under": 80.0})

    # Output is still written before the threshold check.
    assert out_file.exists()


def test_run_service_fail_under_passes(tmp_path):
    doc_file = tmp_path / "doc.json"
    tests_file = tmp_path / "tests.json"
    out_file = tmp_path / "out.json"
    _write(doc_file, _doc_payload())
    _write(tests_file, _tests_payload())

    matrix = run_service(str(doc_file), str(tests_file), str(out_file), {"fail_under": 50.0})

    assert matrix.summary.coverage_pct == 50.0
