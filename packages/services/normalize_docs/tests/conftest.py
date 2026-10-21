# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Shared fixtures: the repository's one copy of `living-doc`'s example `doc-source.json`, changed copies of it, and a
run of `normalize-docs` that reads back what it wrote.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from living_doc_utilities.contracts.generator_ready import GeneratorReadyResult
from living_doc_utilities.contracts.io import read_artifact

from living_doc_service_normalize_docs.service import normalize_docs

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"


@pytest.fixture(name="doc_source")
def _doc_source() -> Path:
    """`living-doc`'s example `doc-source.json`."""
    return FIXTURES / "collector-gh" / "doc-source.json"


@pytest.fixture(name="utilities_golden")
def _utilities_golden() -> Path:
    """`living-doc-utilities`' six golden entities."""
    return FIXTURES / "utilities-golden"


@pytest.fixture(name="changed_copy")
def _changed_copy(tmp_path) -> Callable[..., Path]:
    """Write a copy of a fixture under `tmp_path`, with `change` applied to its parsed JSON, and return its path."""

    def changed_copy(fixture: Path, change: Callable[[dict[str, Any]], object], name: str | None = None) -> Path:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        change(payload)
        path = tmp_path / "in" / (name or fixture.name)
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return changed_copy


@pytest.fixture(name="run_command")
def _run_command(tmp_path) -> Callable[..., GeneratorReadyResult]:
    """Run `normalize-docs` over an input, writing under `tmp_path`, and return the file it wrote as read back."""

    def run_command(input_path: Path, **options: Any) -> GeneratorReadyResult:
        output = tmp_path / "out" / "generator-ready.json"
        normalize_docs(input_path, output, **options)
        result = read_artifact(output, expected="generator-ready")
        assert isinstance(result, GeneratorReadyResult)
        return result

    return run_command
