# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Shared fixtures for the `coverage-matrix` package: the repository's fixture pair, changed copies of it, and the command."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from living_doc_core.readers import read_documentation, read_tests
from living_doc_core.run_context import RUN_VARIABLES
from living_doc_utilities.contracts.coverage_matrix import CoverageMatrixResult
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_tests import UITestsResult

from living_doc_service_coverage_matrix.service import coverage_matrix

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "collector-gh"
DOC_SOURCE = FIXTURES / "doc-source.json"
UI_TESTS = FIXTURES / "ui-tests.json"


@pytest.fixture(autouse=True)
def _no_run_context(monkeypatch):
    for variable in RUN_VARIABLES.values():
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture(name="documentation")
def _documentation() -> DocSourceResult:
    result = read_documentation(DOC_SOURCE)
    assert isinstance(result, DocSourceResult)
    return result


@pytest.fixture(name="ui_tests")
def _ui_tests() -> UITestsResult:
    result = read_tests(UI_TESTS)
    assert isinstance(result, UITestsResult)
    return result


@pytest.fixture(name="changed_copy")
def _changed_copy(tmp_path) -> Callable[..., Path]:
    """Write a copy of a fixture under `tmp_path`, with `change` applied to its parsed JSON, and return its path."""

    def changed_copy(fixture: Path, change: Callable[[dict[str, Any]], object], name: str | None = None) -> Path:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        change(payload)
        path = tmp_path / (name or fixture.name)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return changed_copy


@pytest.fixture(name="run_command")
def _run_command(tmp_path) -> Callable[..., CoverageMatrixResult]:
    """Run the command over a documentation and a tests file, and read the matrix it wrote back."""

    def run_command(
        doc_input: Path = DOC_SOURCE, tests_input: Path = UI_TESTS, view: str = "inner"
    ) -> CoverageMatrixResult:
        output = tmp_path / f"coverage-matrix-{view}.json"
        coverage_matrix([doc_input], tests_input, output, view=view)
        result = read_artifact(output, expected="coverage-matrix")
        assert isinstance(result, CoverageMatrixResult)
        return result

    return run_command
