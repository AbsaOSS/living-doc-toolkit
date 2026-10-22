# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Shared fixtures: the repository's one copy of `living-doc`'s example `doc-source.json`.
"""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "collector-gh"


@pytest.fixture(name="doc_source")
def _doc_source() -> Path:
    """`living-doc`'s example `doc-source.json`."""
    return FIXTURES / "doc-source.json"


@pytest.fixture(name="ui_tests")
def _ui_tests() -> Path:
    """`living-doc`'s example `ui-tests.json`."""
    return FIXTURES / "ui-tests.json"
