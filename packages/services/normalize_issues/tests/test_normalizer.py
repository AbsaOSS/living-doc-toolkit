# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for normalizer module.
"""

from living_doc_service_normalize_issues.normalizer import normalize_sections


def test_normalize_sections_description_synonyms():
    """Test that description synonyms map correctly."""
    # Test 'Description'
    markdown = "## Description\nThis is the description."
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "This is the description."

    # Test 'Overview'
    markdown = "## Overview\nThis is the overview."
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "This is the overview."

    # Test 'Summary'
    markdown = "## Summary\nThis is the summary."
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "This is the summary."


def test_normalize_sections_business_value_synonyms():
    """Test that business value synonyms map correctly."""
    # Test 'Business Value'
    markdown = "## Business Value\nThis adds value."
    result = normalize_sections(markdown)
    assert "business_value" in result
    assert result["business_value"] == "This adds value."

    # Test 'Value'
    markdown = "## Value\nThis is valuable."
    result = normalize_sections(markdown)
    assert "business_value" in result
    assert result["business_value"] == "This is valuable."

    # Test 'Why'
    markdown = "## Why\nBecause reasons."
    result = normalize_sections(markdown)
    assert "business_value" in result
    assert result["business_value"] == "Because reasons."


def test_normalize_sections_preconditions_synonyms():
    """Test that preconditions synonyms map correctly."""
    # Test 'Preconditions'
    markdown = "## Preconditions\nThese are preconditions."
    result = normalize_sections(markdown)
    assert "preconditions" in result
    assert result["preconditions"] == "These are preconditions."

    # Test 'Prerequisites'
    markdown = "## Prerequisites\nThese are prerequisites."
    result = normalize_sections(markdown)
    assert "preconditions" in result
    assert result["preconditions"] == "These are prerequisites."

    # Test 'Setup'
    markdown = "## Setup\nThis is setup."
    result = normalize_sections(markdown)
    assert "preconditions" in result
    assert result["preconditions"] == "This is setup."


def test_normalize_sections_acceptance_criteria_synonyms():
    """Test that acceptance criteria synonyms map correctly."""
    # Test 'Acceptance Criteria'
    markdown = "## Acceptance Criteria\n- Criterion 1\n- Criterion 2"
    result = normalize_sections(markdown)
    assert "acceptance_criteria" in result
    assert "Criterion 1" in result["acceptance_criteria"]

    # Test 'AC'
    markdown = "## AC\n- Test AC"
    result = normalize_sections(markdown)
    assert "acceptance_criteria" in result
    assert "Test AC" in result["acceptance_criteria"]

    # Test 'Done Criteria'
    markdown = "## Done Criteria\n- Done when tested"
    result = normalize_sections(markdown)
    assert "acceptance_criteria" in result
    assert "Done when tested" in result["acceptance_criteria"]


def test_normalize_sections_user_guide_synonyms():
    """Test that user guide synonyms map correctly."""
    # Test 'User Guide'
    markdown = "## User Guide\nFollow these steps."
    result = normalize_sections(markdown)
    assert "user_guide" in result
    assert result["user_guide"] == "Follow these steps."

    # Test 'How To'
    markdown = "## How To\nDo it this way."
    result = normalize_sections(markdown)
    assert "user_guide" in result
    assert result["user_guide"] == "Do it this way."

    # Test 'Instructions'
    markdown = "## Instructions\nRead carefully."
    result = normalize_sections(markdown)
    assert "user_guide" in result
    assert result["user_guide"] == "Read carefully."


def test_normalize_sections_connections_synonyms():
    """Test that connections synonyms map correctly."""
    # Test 'Connections'
    markdown = "## Connections\nRelated to #123"
    result = normalize_sections(markdown)
    assert "connections" in result
    assert result["connections"] == "Related to #123"

    # Test 'Related'
    markdown = "## Related\nSee issue #456"
    result = normalize_sections(markdown)
    assert "connections" in result
    assert result["connections"] == "See issue #456"

    # Test 'Links'
    markdown = "## Links\nhttps://example.com"
    result = normalize_sections(markdown)
    assert "connections" in result
    assert result["connections"] == "https://example.com"


def test_normalize_sections_last_edited_synonyms():
    """Test that last edited synonyms map correctly."""
    # Test 'Last Edited'
    markdown = "## Last Edited\n2026-01-15"
    result = normalize_sections(markdown)
    assert "last_edited" in result
    assert result["last_edited"] == "2026-01-15"

    # Test 'History'
    markdown = "## History\nVersion history"
    result = normalize_sections(markdown)
    assert "last_edited" in result
    assert result["last_edited"] == "Version history"

    # Test 'Changes'
    markdown = "## Changes\nRecent changes"
    result = normalize_sections(markdown)
    assert "last_edited" in result
    assert result["last_edited"] == "Recent changes"


def test_normalize_sections_case_insensitive():
    """Test that heading matching is case-insensitive."""
    markdown = "## DESCRIPTION\nUpper case heading"
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "Upper case heading"

    markdown = "## description\nLower case heading"
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "Lower case heading"

    markdown = "## DeScrIpTioN\nMixed case heading"
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "Mixed case heading"


def test_normalize_sections_unknown_heading_appended_to_description():
    """Test that unknown headings are appended to description."""
    markdown = "## Unknown Heading\nThis is unknown content."
    result = normalize_sections(markdown)
    assert "description" in result
    assert "### Unknown Heading" in result["description"]
    assert "This is unknown content." in result["description"]


def test_normalize_sections_multiple_unknown_headings():
    """Test that multiple unknown headings are appended to description."""
    markdown = """## First Unknown
Content 1

## Second Unknown
Content 2"""
    result = normalize_sections(markdown)
    assert "description" in result
    assert "### First Unknown" in result["description"]
    assert "Content 1" in result["description"]
    assert "### Second Unknown" in result["description"]
    assert "Content 2" in result["description"]


def test_normalize_sections_content_before_first_heading():
    """Test that content before first heading is assigned to description."""
    markdown = """Some introductory text.

## Business Value
This is value."""
    result = normalize_sections(markdown)
    assert "description" in result
    assert "Some introductory text." in result["description"]
    assert "business_value" in result
    assert result["business_value"] == "This is value."


def test_normalize_sections_mixed_known_and_unknown():
    """Test mixed known and unknown headings."""
    markdown = """## Description
This is the description.

## Custom Section
This is custom.

## Business Value
This is value."""
    result = normalize_sections(markdown)
    assert "description" in result
    assert "This is the description." in result["description"]
    assert "### Custom Section" in result["description"]
    assert "This is custom." in result["description"]
    assert "business_value" in result
    assert result["business_value"] == "This is value."


def test_normalize_sections_empty_body():
    """Test handling of empty body."""
    result = normalize_sections("")
    assert "description" in result
    assert result["description"] is None


def test_normalize_sections_none_body():
    """Test handling of None body."""
    result = normalize_sections(None)
    assert "description" in result
    assert result["description"] is None


def test_normalize_sections_no_headings():
    """Test markdown with no headings."""
    markdown = "Just some plain text with no headings."
    result = normalize_sections(markdown)
    assert "description" in result
    assert result["description"] == "Just some plain text with no headings."


def test_normalize_sections_deterministic():
    """Test that same input produces same output."""
    markdown = """## Description
Content 1

## Business Value
Content 2

## Unknown
Content 3"""
    result1 = normalize_sections(markdown)
    result2 = normalize_sections(markdown)
    assert result1 == result2


def test_normalize_sections_preserves_markdown_formatting():
    """Test that markdown formatting is preserved."""
    markdown = """## Description
This has **bold** and *italic* text.

- List item 1
- List item 2

| Table | Header |
|-------|--------|
| Row 1 | Data 1 |

[Link](https://example.com)"""
    result = normalize_sections(markdown)
    assert "description" in result
    assert "**bold**" in result["description"]
    assert "*italic*" in result["description"]
    assert "- List item 1" in result["description"]
    assert "| Table | Header |" in result["description"]
    assert "[Link](https://example.com)" in result["description"]


def test_normalize_sections_empty_section_content():
    """Test handling of sections with empty content."""
    markdown = """## Description

## Business Value
Actual content"""
    result = normalize_sections(markdown)
    # Empty Description section should not be included
    assert "description" not in result or result.get("description") is None
    assert "business_value" in result
    assert result["business_value"] == "Actual content"
