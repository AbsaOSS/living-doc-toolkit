# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Shared fixtures: the repository's one copy of `living-doc`'s example collector-gh outputs, and changed copies of it.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
