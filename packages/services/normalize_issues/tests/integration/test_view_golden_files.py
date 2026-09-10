# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Integration tests: a single mined input rendered into both the inner and release views.
"""

import json
from pathlib import Path

import pytest

from living_doc_service_normalize_issues.service import run_service

_FIXTURES = Path(__file__).resolve().parents[5] / "tests" / "fixtures" / "views"


def _run(view: str, tmp_path: Path) -> dict:
    output_file = tmp_path / f"{view}.json"
    run_service(
        str(_FIXTURES / "input.json"),
        str(output_file),
        {"document_title": "Living Documentation - views", "document_version": "1.0.0", "view": view},
    )
    actual = json.loads(output_file.read_text(encoding="utf-8"))
    actual["meta"]["generated_at"] = "DYNAMIC_TIMESTAMP"
    for trace_step in actual["meta"]["audit"]["trace"]:
        trace_step["started_at"] = "DYNAMIC_TIMESTAMP"
        trace_step["finished_at"] = "DYNAMIC_TIMESTAMP"
    return actual


@pytest.mark.parametrize("view", ["inner", "release"])
def test_view_matches_golden(view, tmp_path):
    """Each view's output matches its committed golden fixture."""
    expected = json.loads((_FIXTURES / f"expected_{view}.json").read_text(encoding="utf-8"))
    assert _run(view, tmp_path) == expected


def test_inner_keeps_planned_entities_and_deprecated_acs(tmp_path):
    """Inner view retains a planned entity and a deprecated acceptance criterion."""
    actual = _run("inner", tmp_path)

    story_ids = [s["id"] for s in actual["content"]["user_stories"]]
    assert "github:AbsaOSS/living-doc-toolkit#11" in story_ids  # planned entity

    shipped = next(s for s in actual["content"]["user_stories"] if s["id"] == "github:AbsaOSS/living-doc-toolkit#10")
    ac_states = [ac["state"] for ac in shipped["sections"]["acceptance_criteria"]]
    assert "deprecated" in ac_states
    assert actual["meta"]["view"] == {
        "view": "inner",
        "filtered_user_stories": 0,
        "filtered_acceptance_criteria": 0,
    }


def test_release_drops_planned_entities_and_planned_in_review_deprecated_acs(tmp_path):
    """Release view removes planned/in_review entities and planned/in_review/deprecated ACs (issue #77)."""
    actual = _run("release", tmp_path)

    story_ids = [s["id"] for s in actual["content"]["user_stories"]]
    assert story_ids == ["github:AbsaOSS/living-doc-toolkit#10"]

    shipped = actual["content"]["user_stories"][0]
    ac_states = [ac["state"] for ac in shipped["sections"]["acceptance_criteria"]]
    assert ac_states == ["Active"]

    assert actual["meta"]["view"] == {
        "view": "release",
        "filtered_user_stories": 2,
        "filtered_acceptance_criteria": 2,
    }
    assert actual["meta"]["selection_summary"] == {"total_items": 3, "included_items": 1, "excluded_items": 2}
