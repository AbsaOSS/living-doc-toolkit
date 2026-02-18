#!/usr/bin/env python3
#
# Copyright 2026 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Compatibility verification script.

This script tests the normalization service with different collector-gh
versions to verify compatibility warnings are generated correctly.
"""

import json
import sys
from pathlib import Path


def test_version_fixture(version: str, expected_warnings: bool) -> bool:
    """
    Test normalization with a specific collector-gh version fixture.

    Args:
        version: Version string (e.g., "v0.9.0", "v1.0.0", "v2.0.0")
        expected_warnings: Whether VERSION_MISMATCH warnings are expected

    Returns:
        True if test passes, False otherwise
    """
    print(f"\nTesting {version}:")
    print("-" * 60)

    # Define paths
    repo_root = Path(__file__).parent.parent
    input_file = repo_root / "tests" / "fixtures" / "collector_gh" / version / "input" / "doc-issues.json"
    output_file = Path(f"/tmp/test_compatibility_{version}_output.json")

    # Verify input file exists
    if not input_file.exists():
        print(f"✗ Input file not found: {input_file}")
        return False

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    # Try to import and run the service
    try:
        from living_doc_service_normalize_issues.service import run_service

        options = {}
        run_service(str(input_file), str(output_file), options)
    except ImportError:
        print("✗ Cannot import living_doc_service_normalize_issues")
        print("  Packages may not be installed. Run:")
        print("  pip install -e packages/core -e packages/datasets_pdf")
        print("  pip install -e packages/adapters/collector_gh -e packages/services/normalize_issues")
        return False
    except Exception as e:  # pylint: disable=broad-except
        print(f"✗ Normalization failed: {e}")
        return False

    # Load output and check warnings
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            output = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"✗ Failed to load output file: {e}")
        return False

    # Check if audit trace exists
    if "audit" not in output["meta"] or "trace" not in output["meta"]["audit"]:
        print("✗ No audit trace found in output")
        return False

    # Get warnings from the first trace step (normalization step)
    warnings = []
    for trace_step in output["meta"]["audit"]["trace"]:
        warnings.extend(trace_step.get("warnings", []))

    # Check if VERSION_MISMATCH warnings exist
    version_warnings = [w for w in warnings if w.get("code") == "VERSION_MISMATCH"]

    if expected_warnings:
        if version_warnings:
            print(f"✓ Expected warnings found: {len(version_warnings)}")
            for warning in version_warnings:
                print(f"  - [{warning['code']}] {warning['message']}")
            return True
        print("✗ Expected VERSION_MISMATCH warnings but none found")
        return False

    if not version_warnings:
        print("✓ No VERSION_MISMATCH warnings (as expected)")
        return True

    print(f"✗ Unexpected VERSION_MISMATCH warnings found: {len(version_warnings)}")
    for warning in version_warnings:
        print(f"  - [{warning['code']}] {warning['message']}")
    return False


def main() -> int:
    """Run compatibility verification for all test versions."""
    print("=" * 60)
    print("Collector-GH Version Compatibility Verification")
    print("=" * 60)

    results = []

    # Test v0.9.0 (below supported range - should warn)
    results.append(("v0.9.0", test_version_fixture("v0.9.0", expected_warnings=True)))

    # Test v1.0.0 (within supported range - should not warn)
    results.append(("v1.0.0", test_version_fixture("v1.0.0", expected_warnings=False)))

    # Test v2.0.0 (above supported range - should warn)
    results.append(("v2.0.0", test_version_fixture("v2.0.0", expected_warnings=True)))

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

    print("\n✗ Some compatibility tests failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
