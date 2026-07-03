# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the loader module."""

import json

import pytest

from living_doc_core.errors import FileIOError, InvalidInputError

from living_doc_service_coverage_matrix.loader import load_doc_input, load_tests_input


def _write(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def test_load_doc_input_bare_array(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(doc_file, [{"id": "org/repo/US-1", "acceptance_criteria": []}])

    result = load_doc_input(str(doc_file))

    assert len(result["user_stories"]) == 1
    assert result["user_stories"][0]["id"] == "org/repo/US-1"
    assert result["functionalities"] == []
    assert result["features"] == []


def test_load_doc_input_legacy_items_envelope(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(doc_file, {"items": [{"id": "org/repo/US-1", "acceptance_criteria": []}], "metadata": {}})

    result = load_doc_input(str(doc_file))

    assert len(result["user_stories"]) == 1
    assert result["user_stories"][0]["id"] == "org/repo/US-1"
    assert result["functionalities"] == []
    assert result["features"] == []


def test_load_doc_input_doc_source_envelope(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(
        doc_file,
        {
            "user_stories": [{"id": "org/repo/US-1", "acceptance_criteria": []}],
            "functionalities": [{"id": "org/repo/FUNC-001", "acceptance_criteria": []}],
            "features": [{"id": "org/repo/FEAT-001"}],
            "metadata": {},
        },
    )

    result = load_doc_input(str(doc_file))

    assert result["user_stories"][0]["id"] == "org/repo/US-1"
    assert result["functionalities"][0]["id"] == "org/repo/FUNC-001"
    assert result["features"][0]["id"] == "org/repo/FEAT-001"


def test_load_doc_input_invalid_shape(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(doc_file, {"no_items": True})

    with pytest.raises(InvalidInputError):
        load_doc_input(str(doc_file))


def _valid_metadata():
    return {
        "producer": {"name": "collector-gh", "version": "1.0.0", "build": None},
        "run": {
            "run_id": None,
            "run_attempt": None,
            "actor": None,
            "workflow": None,
            "ref": None,
            "sha": None,
        },
        "source": {"systems": [], "repositories": [], "organization": None, "enterprise": None},
        "original_metadata": {},
    }


def _valid_user_story():
    return {
        "id": "org/repo/US-1",
        "repository_name": "org/repo",
        "title": "A story",
        "state": "open",
        "tags": [],
        "url": None,
        "timestamps": None,
        "acceptance_criteria": [],
    }


def test_load_doc_input_doc_source_envelope_schema_valid(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(
        doc_file,
        {
            "user_stories": [_valid_user_story()],
            "functionalities": [{"id": "org/repo/FUNC-001", "repository_name": "org/repo", "title": "F"}],
            "features": [{"id": "org/repo/FEAT-001", "repository_name": "org/repo", "title": "Feat"}],
            "metadata": _valid_metadata(),
            "warnings": [],
        },
    )

    result = load_doc_input(str(doc_file))

    assert result["user_stories"][0]["id"] == "org/repo/US-1"
    assert result["functionalities"][0]["id"] == "org/repo/FUNC-001"
    assert result["features"][0]["id"] == "org/repo/FEAT-001"


def test_load_doc_input_doc_source_envelope_schema_invalid(tmp_path):
    doc_file = tmp_path / "doc.json"
    bad_story = {"id": "org/repo/US-1"}  # missing required fields
    _write(
        doc_file,
        {
            "user_stories": [bad_story],
            "functionalities": [],
            "features": [],
            "metadata": _valid_metadata(),
            "warnings": [],
        },
    )

    with pytest.raises(InvalidInputError, match="schema validation"):
        load_doc_input(str(doc_file))


def test_load_doc_input_missing_file(tmp_path):
    with pytest.raises(FileIOError):
        load_doc_input(str(tmp_path / "missing.json"))


def test_load_tests_input_envelope(tmp_path):
    tests_file = tmp_path / "tests.json"
    _write(tests_file, {"items": [{"id": "s1", "us_id": "US-1"}]})

    items = load_tests_input(str(tests_file))

    assert len(items) == 1
    assert items[0]["us_id"] == "US-1"


def test_load_tests_input_missing_items(tmp_path):
    tests_file = tmp_path / "tests.json"
    _write(tests_file, [{"id": "s1"}])

    with pytest.raises(InvalidInputError):
        load_tests_input(str(tests_file))


def test_load_tests_input_malformed_json(tmp_path):
    tests_file = tmp_path / "tests.json"
    with open(tests_file, "w", encoding="utf-8") as f:
        f.write("{ not valid json ")

    with pytest.raises(InvalidInputError):
        load_tests_input(str(tests_file))
