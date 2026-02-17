#!/usr/bin/env python3
# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Verification script for golden file test.

This script runs the normalization service with the golden input file
and compares the output to the expected golden output.
"""

import json
import sys
from pathlib import Path

from living_doc_service_normalize_issues.service import run_service


def normalize_timestamps(data: dict) -> None:
    """Remove dynamic timestamps for comparison."""
    if "meta" in data:
        data["meta"]["generated_at"] = "DYNAMIC_TIMESTAMP"
        if data["meta"].get("audit"):
            for trace_step in data["meta"]["audit"]["trace"]:
                if trace_step.get("started_at"):
                    trace_step["started_at"] = "DYNAMIC_TIMESTAMP"
                if trace_step.get("finished_at"):
                    trace_step["finished_at"] = "DYNAMIC_TIMESTAMP"


def main() -> int:
    """Run golden file verification."""
    # Get paths
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent
    fixtures_dir = package_dir / "tests" / "fixtures" / "golden"

    input_file = fixtures_dir / "input.json"
    expected_file = fixtures_dir / "expected_output.json"
    output_file = Path("/tmp/verify_golden_output.json")

    print("Golden File Verification")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Expected: {expected_file}")
    print(f"Output: {output_file}")
    print()

    # Run normalization
    try:
        options = {"document_title": "Living Documentation - AbsaOSS/living-doc-toolkit", "document_version": "1.0.0"}
        run_service(str(input_file), str(output_file), options)
    except Exception as e:
        print(f"ERROR: Normalization failed: {e}")
        return 1

    # Load outputs
    try:
        with open(expected_file, "r", encoding="utf-8") as f:
            expected = json.load(f)

        with open(output_file, "r", encoding="utf-8") as f:
            actual = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load output files: {e}")
        return 1

    # Normalize timestamps
    normalize_timestamps(actual)

    # Compare
    if actual == expected:
        print("✓ Output matches expected golden file")
        print(f"  - User stories: {len(actual['content']['user_stories'])}")
        print(f"  - Document title: {actual['meta']['document_title']}")
        print(f"  - Document version: {actual['meta']['document_version']}")
        return 0
    else:
        print("✗ Output does NOT match expected golden file")
        print()
        print("Differences found. Run diff to see details:")
        print(f"  diff {expected_file} {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
