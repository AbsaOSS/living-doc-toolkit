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
Golden file verification script.

This script runs the normalization service with golden input fixtures
and compares the output to expected golden output files.
"""

import json
import sys
from pathlib import Path


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


def run_golden_test(version: str) -> bool:
    """
    Run golden file test for a specific version.

    Args:
        version: Version string (e.g., "v1.0.0")

    Returns:
        True if test passes, False otherwise
    """
    print(f"\nTesting {version}:")
    print("-" * 60)

    # Define paths
    repo_root = Path(__file__).parent.parent
    input_file = repo_root / "tests" / "fixtures" / "collector_gh" / version / "input" / "doc-issues.json"
    expected_file = repo_root / "tests" / "fixtures" / "golden" / version / "expected_output.json"
    output_file = Path(f"/tmp/verify_golden_{version}_output.json")

    # Verify input file exists
    if not input_file.exists():
        print(f"✗ Input file not found: {input_file}")
        return False

    # Verify expected output file exists
    if not expected_file.exists():
        print(f"✗ Expected output file not found: {expected_file}")
        return False

    print(f"Input: {input_file}")
    print(f"Expected: {expected_file}")
    print(f"Output: {output_file}")

    # Try to import and run the service
    try:
        from living_doc_service_normalize_issues.service import run_service

        options = {
            "document_title": f"Living Documentation - {version} Test",
            "document_version": version.replace("v", ""),
        }
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

    # Load outputs
    try:
        with open(expected_file, "r", encoding="utf-8") as f:
            expected = json.load(f)

        with open(output_file, "r", encoding="utf-8") as f:
            actual = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"✗ Failed to load output files: {e}")
        return False

    # Normalize timestamps
    normalize_timestamps(actual)

    # Compare
    if actual == expected:
        print(f"✓ Output matches expected golden file")
        print(f"  - User stories: {len(actual['content']['user_stories'])}")
        print(f"  - Document title: {actual['meta']['document_title']}")
        print(f"  - Document version: {actual['meta']['document_version']}")
        return True

    print("✗ Output does NOT match expected golden file")
    print()
    print("To see differences, run:")
    print(f"  diff {expected_file} {output_file}")
    return False


def main() -> int:
    """Run golden file verification for all versions."""
    print("=" * 60)
    print("Golden File Verification")
    print("=" * 60)

    results = []

    # Test v1.0.0
    results.append(("v1.0.0", run_golden_test("v1.0.0")))

    # Test v1.2.0
    results.append(("v1.2.0", run_golden_test("v1.2.0")))

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
        print("\n✓ All golden file tests passed")
        return 0

    print("\n✗ Some golden file tests failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
