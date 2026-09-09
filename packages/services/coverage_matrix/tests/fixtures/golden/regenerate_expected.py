# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Regenerate ``expected_coverage_matrix.json`` from the golden input fixtures.

Run this after ``../generate_golden_inputs.py`` refreshes ``doc_source.json`` /
``ui_tests.json`` from real collector output. The dynamic ``generated_at`` field is
pinned to ``PLACEHOLDER`` to match the integration test's normalisation.

Usage::

    python packages/services/coverage_matrix/tests/fixtures/golden/regenerate_expected.py
"""

import json
import tempfile
from pathlib import Path

from living_doc_service_coverage_matrix.service import run_service

GOLDEN_DIR = Path(__file__).resolve().parent


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_file = Path(tmp) / "coverage-matrix.json"
        run_service(
            str(GOLDEN_DIR / "doc_source.json"),
            str(GOLDEN_DIR / "ui_tests.json"),
            str(out_file),
            {},
        )
        matrix = json.loads(out_file.read_text(encoding="utf-8"))

    matrix["generated_at"] = "PLACEHOLDER"
    (GOLDEN_DIR / "expected_coverage_matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {GOLDEN_DIR / 'expected_coverage_matrix.json'}")


if __name__ == "__main__":
    main()
