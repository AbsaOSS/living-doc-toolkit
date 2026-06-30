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

    items = load_doc_input(str(doc_file))

    assert len(items) == 1
    assert items[0]["id"] == "org/repo/US-1"


def test_load_doc_input_envelope(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(doc_file, {"items": [{"id": "org/repo/US-1", "acceptance_criteria": []}], "metadata": {}})

    items = load_doc_input(str(doc_file))

    assert len(items) == 1
    assert items[0]["id"] == "org/repo/US-1"


def test_load_doc_input_invalid_shape(tmp_path):
    doc_file = tmp_path / "doc.json"
    _write(doc_file, {"no_items": True})

    with pytest.raises(InvalidInputError):
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
