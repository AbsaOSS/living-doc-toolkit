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

_FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "collector_gh"


def discover_version_fixtures() -> list[str]:
    """
    Discover every collector-gh fixture directory (``tests/fixtures/collector_gh/v*/``).

    Matches the discovery rule documented in ``.claude/agents/test-author.md`` — the version
    list is never hard-coded here, so a new ``v<X.Y.Z>/`` fixture is picked up automatically.

    Returns:
        Sorted directory names (e.g. ``["v0.1.0", "v1.0.0", "v1.2.0", "v2.0.0"]``).
    """
    return sorted(d.name for d in _FIXTURES_DIR.glob("v*") if (d / "input" / "doc-issues.json").is_file())


def expected_warning_for(version_dir: str) -> bool:
    """
    Whether the fixture's producer version falls outside the adapter's confirmed range.

    Derived from the live compatibility check (``CONFIRMED_MIN`` / ``CONFIRMED_MAX`` in
    ``compatibility.py``), so the expectation can never drift from the code under test.

    Args:
        version_dir: Fixture directory name (e.g. ``"v1.2.0"``).

    Returns:
        True if a ``VERSION_MISMATCH`` warning is expected for that fixture.
    """
    from living_doc_adapter_collector_gh.compatibility import check_compatibility

    payload = json.loads((_FIXTURES_DIR / version_dir / "input" / "doc-issues.json").read_text(encoding="utf-8"))
    producer_version = payload["metadata"]["producer"]["version"]
    return any(w.code == "VERSION_MISMATCH" for w in check_compatibility(producer_version))


def test_version_fixture(version: str, expected_warnings: bool) -> bool:
    """
    Test normalization with a specific collector-gh version fixture.

    Args:
        version: Version string (e.g., "v0.1.0", "v1.0.0", "v2.0.0")
        expected_warnings: Whether VERSION_MISMATCH warnings are expected

    Returns:
        True if test passes, False otherwise
    """
    print(f"\nTesting {version}:")
    print("-" * 60)

    # Define paths
    input_file = _FIXTURES_DIR / version / "input" / "doc-issues.json"
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
    """Run compatibility verification for every discovered collector-gh fixture."""
    print("=" * 60)
    print("Collector-GH Version Compatibility Verification")
    print("=" * 60)

    version_dirs = discover_version_fixtures()
    if not version_dirs:
        print(f"\n✗ No fixtures found under {_FIXTURES_DIR}")
        return 1

    try:
        expectations = {v: expected_warning_for(v) for v in version_dirs}
    except ImportError:
        print("✗ Cannot import living_doc_adapter_collector_gh")
        print("  Packages may not be installed. Run:")
        print("  pip install -e packages/core -e packages/datasets_pdf")
        print("  pip install -e packages/adapters/collector_gh -e packages/services/normalize_issues")
        return 1

    results = []
    for version in version_dirs:
        expected = expectations[version]
        note = "outside confirmed range - should warn" if expected else "within confirmed range - should not warn"
        print(f"\n({version}: {note})")
        results.append((version, test_version_fixture(version, expected_warnings=expected)))

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
