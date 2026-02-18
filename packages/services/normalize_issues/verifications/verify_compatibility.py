#!/usr/bin/env python3
# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Verification script for collector-gh version compatibility.

This script tests the normalization service with different collector-gh
versions to verify compatibility warnings.
"""

import json
import sys
from pathlib import Path

from living_doc_service_normalize_issues.service import run_service


def test_version(version: str, expected_warnings: bool) -> bool:
    """Test normalization with a specific collector-gh version."""
    print(f"\nTesting collector-gh v{version}:")
    print("-" * 40)

    # Create test input with specified version
    input_data = {
        "metadata": {
            "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": version},
            "run": {
                "run_id": None,
                "run_attempt": None,
                "actor": None,
                "workflow": None,
                "ref": None,
                "sha": None,
            },
            "source": {
                "systems": ["github"],
                "repositories": ["github:test/repo"],
                "organization": None,
                "enterprise": None,
            },
        },
        "issues": [
            {
                "number": 1,
                "title": "Test Issue",
                "state": "open",
                "labels": [],
                "html_url": "https://github.com/test/repo/issues/1",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "body": "## Description\nTest content.",
            }
        ],
    }

    # Write input file
    input_file = Path(f"/tmp/test_input_v{version}.json")
    output_file = Path(f"/tmp/test_output_v{version}.json")

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(input_data, f)

    # Run normalization
    try:
        options = {}
        run_service(str(input_file), str(output_file), options)

        # Load output to check warnings
        with open(output_file, "r", encoding="utf-8") as f:
            output = json.load(f)

        warnings = output["meta"]["audit"]["trace"][0]["warnings"]

        if expected_warnings:
            if warnings:
                print(f"✓ Expected warnings found: {len(warnings)}")
                for warning in warnings:
                    print(f"  - [{warning['code']}] {warning['message']}")
                return True
            else:
                print("✗ Expected warnings but none found")
                return False
        else:
            if not warnings:
                print("✓ No warnings (as expected)")
                return True
            else:
                print(f"✗ Unexpected warnings found: {len(warnings)}")
                for warning in warnings:
                    print(f"  - [{warning['code']}] {warning['message']}")
                return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main() -> int:
    """Run compatibility verification."""
    print("Collector-GH Version Compatibility Verification")
    print("=" * 60)

    results = []

    # Test v0.9.0 (should warn - below supported range)
    results.append(("v0.9.0", test_version("0.9.0", expected_warnings=True)))

    # Test v1.0.0 (should pass with no warnings)
    results.append(("v1.0.0", test_version("1.0.0", expected_warnings=False)))

    # Test v2.0.0 (should warn - above supported range)
    results.append(("v2.0.0", test_version("2.0.0", expected_warnings=True)))

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    all_passed = True
    for version, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {version}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All compatibility tests passed")
        return 0
    else:
        print("\n✗ Some compatibility tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
