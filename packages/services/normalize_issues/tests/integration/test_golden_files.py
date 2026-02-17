# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Integration tests with golden files.
"""

import json
from pathlib import Path

from living_doc_service_normalize_issues.service import run_service


def test_golden_files(tmp_path):
    """Test normalization with golden input/output files."""
    # Get fixture paths
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "golden"
    input_file = fixtures_dir / "input.json"
    expected_output_file = fixtures_dir / "expected_output.json"

    # Output file in temp directory
    output_file = tmp_path / "output.json"

    # Run service
    options = {"document_title": "Living Documentation - AbsaOSS/living-doc-toolkit", "document_version": "1.0.0"}
    run_service(str(input_file), str(output_file), options)

    # Load expected and actual output
    with open(expected_output_file, "r", encoding="utf-8") as f:
        expected = json.load(f)

    with open(output_file, "r", encoding="utf-8") as f:
        actual = json.load(f)

    # Normalize dynamic fields for comparison
    actual["meta"]["generated_at"] = "DYNAMIC_TIMESTAMP"
    if actual["meta"]["audit"]:
        for trace_step in actual["meta"]["audit"]["trace"]:
            if trace_step.get("started_at"):
                trace_step["started_at"] = "DYNAMIC_TIMESTAMP"
            if trace_step.get("finished_at"):
                trace_step["finished_at"] = "DYNAMIC_TIMESTAMP"

    # Compare outputs
    assert actual == expected, "Output does not match expected golden file"

    # Verify structure
    assert actual["schema_version"] == "1.0"
    assert len(actual["content"]["user_stories"]) == 5
    assert actual["meta"]["document_title"] == "Living Documentation - AbsaOSS/living-doc-toolkit"
    assert actual["meta"]["document_version"] == "1.0.0"

    # Verify first user story has normalized sections
    story1 = actual["content"]["user_stories"][0]
    assert story1["id"] == "github:AbsaOSS/living-doc-toolkit#1"
    assert story1["sections"]["description"] == "Implement secure user authentication for the application."
    assert story1["sections"]["business_value"] == "Provides secure access control and user management capabilities."
    assert story1["sections"]["preconditions"] == "- Database schema updated\n- OAuth provider configured"
    assert "User can log in with email and password" in story1["sections"]["acceptance_criteria"]

    # Verify second user story uses synonyms
    story2 = actual["content"]["user_stories"][1]
    assert story2["sections"]["description"] == "Add dark mode theme support to improve user experience."
    assert story2["sections"]["business_value"] == "Many users prefer dark mode for reduced eye strain."
    assert "Theme toggle button in settings" in story2["sections"]["acceptance_criteria"]

    # Verify third user story has no headings (content before first heading)
    story3 = actual["content"]["user_stories"][2]
    assert (
        story3["sections"]["description"]
        == "Pagination is not working correctly on the users list page. When clicking page 2, it shows page 1 content."
    )

    # Verify fourth user story has custom section appended to description
    story4 = actual["content"]["user_stories"][3]
    assert "Create comprehensive API documentation." in story4["sections"]["description"]
    assert "### Custom Section" in story4["sections"]["description"]
    assert "This is a custom section that should be appended to description." in story4["sections"]["description"]
    assert story4["sections"]["user_guide"] is not None
    assert story4["sections"]["connections"] is not None

    # Verify fifth user story with null body
    story5 = actual["content"]["user_stories"][4]
    assert story5["sections"]["description"] is None

    # Verify audit trail
    assert actual["meta"]["audit"]["schema_version"] == "1.0"
    assert actual["meta"]["audit"]["producer"]["name"] == "AbsaOSS/living-doc-collector-gh"
    assert len(actual["meta"]["audit"]["trace"]) == 1
    assert actual["meta"]["audit"]["trace"][0]["step"] == "normalization"
