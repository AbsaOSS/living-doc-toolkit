# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Shared fixtures for the `normalize-tests` package."""

from pathlib import Path

import pytest
from living_doc_core.readers import read_tests
from living_doc_core.run_context import RUN_VARIABLES
from living_doc_utilities.contracts.io import read_artifact
from living_doc_utilities.contracts.ui_test_catalog import UiTestCatalogResult
from living_doc_utilities.contracts.ui_tests import UITestsResult

from living_doc_service_normalize_tests.service import normalize_tests

FIXTURE = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "collector-gh" / "ui-tests.json"


@pytest.fixture(autouse=True)
def _no_run_context(monkeypatch):
    for variable in RUN_VARIABLES.values():
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture(name="ui_tests")
def _ui_tests() -> UITestsResult:
    result = read_tests(FIXTURE)
    assert isinstance(result, UITestsResult)
    return result


@pytest.fixture(name="run_command")
def _run_command(tmp_path):
    def run_command(input_path: Path) -> UiTestCatalogResult:
        output = tmp_path / "ui-test-catalog.json"
        normalize_tests(input_path, output)
        result = read_artifact(output, expected="ui-test-catalog")
        assert isinstance(result, UiTestCatalogResult)
        return result

    return run_command
