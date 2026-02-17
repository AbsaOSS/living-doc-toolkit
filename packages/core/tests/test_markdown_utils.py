# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for markdown utilities.
"""

from living_doc_core.markdown_utils import extract_lists, normalize_heading, split_by_headings


def test_split_by_headings_with_multiple_h2():
    """Test splitting markdown with multiple H2 headings."""
    markdown = """## First Heading
Content for first section.

## Second Heading
Content for second section.

## Third Heading
Content for third section."""

    result = split_by_headings(markdown, level=2)

    assert "First Heading" in result
    assert "Second Heading" in result
    assert "Third Heading" in result
    assert result["First Heading"] == "Content for first section."
    assert result["Second Heading"] == "Content for second section."
    assert result["Third Heading"] == "Content for third section."


def test_split_by_headings_with_content_before_first_heading():
    """Test splitting markdown with content before the first heading."""
    markdown = """Some introductory text.
More intro content.

## First Heading
Section content."""

    result = split_by_headings(markdown, level=2)

    assert "" in result
    assert result[""] == "Some introductory text.\nMore intro content."
    assert "First Heading" in result
    assert result["First Heading"] == "Section content."


def test_split_by_headings_with_no_headings():
    """Test splitting markdown with no headings."""
    markdown = "Just some plain text with no headings."

    result = split_by_headings(markdown, level=2)

    assert "" in result
    assert result[""] == markdown


def test_split_by_headings_with_different_levels():
    """Test splitting markdown with H3 headings."""
    markdown = """### First H3
Content under H3.

### Second H3
More H3 content."""

    result = split_by_headings(markdown, level=3)

    assert "First H3" in result
    assert "Second H3" in result
    assert result["First H3"] == "Content under H3."
    assert result["Second H3"] == "More H3 content."


def test_split_by_headings_with_empty_sections():
    """Test splitting markdown with empty sections."""
    markdown = """## Empty Section

## Another Empty

## Section With Content
Some content here."""

    result = split_by_headings(markdown, level=2)

    assert "Empty Section" in result
    assert "Another Empty" in result
    assert "Section With Content" in result
    assert result["Empty Section"] == ""
    assert result["Another Empty"] == ""
    assert result["Section With Content"] == "Some content here."


def test_split_by_headings_ignores_wrong_level_headings():
    """Test that splitting by H2 ignores H1 and H3 headings."""
    markdown = """# H1 Heading
Some content.

## H2 Heading
H2 content.

### H3 Heading
H3 content."""

    result = split_by_headings(markdown, level=2)

    # Should only split on H2
    assert "H2 Heading" in result
    assert "H1 Heading" not in result
    assert "H3 Heading" not in result
    # Content before first H2 (including H1) goes to empty key
    assert "" in result


def test_split_by_headings_preserves_formatting():
    """Test that content formatting is preserved."""
    markdown = """## Code Section
Here is some code:

```python
def hello():
    print("world")
```

## List Section
- Item 1
- Item 2"""

    result = split_by_headings(markdown, level=2)

    assert "Code Section" in result
    assert "```python" in result["Code Section"]
    assert "List Section" in result
    assert "- Item 1" in result["List Section"]


def test_normalize_heading():
    """Test normalize_heading function."""
    assert normalize_heading("Test Heading") == "test heading"
    assert normalize_heading("  Spaced  ") == "spaced"
    assert normalize_heading("UPPERCASE") == "uppercase"
    assert normalize_heading("Mixed Case") == "mixed case"


def test_normalize_heading_with_special_chars():
    """Test normalize_heading with special characters."""
    assert normalize_heading("Heading: With Punctuation!") == "heading: with punctuation!"
    assert normalize_heading("  Multiple   Spaces  ") == "multiple   spaces"


def test_extract_lists_with_dash_bullets():
    """Test extracting bullet lists with dash markers."""
    markdown = """Some text
- First item
- Second item
- Third item
More text"""

    items = extract_lists(markdown)
    assert items == ["First item", "Second item", "Third item"]


def test_extract_lists_with_asterisk_bullets():
    """Test extracting bullet lists with asterisk markers."""
    markdown = """* Item A
* Item B
* Item C"""

    items = extract_lists(markdown)
    assert items == ["Item A", "Item B", "Item C"]


def test_extract_lists_with_mixed_bullets():
    """Test extracting lists with mixed bullet markers."""
    markdown = """- Dash item
* Asterisk item
- Another dash"""

    items = extract_lists(markdown)
    assert items == ["Dash item", "Asterisk item", "Another dash"]


def test_extract_lists_with_no_bullets():
    """Test extracting lists from text with no bullets."""
    markdown = "Just plain text with no bullets."

    items = extract_lists(markdown)
    assert items == []


def test_extract_lists_ignores_empty_bullets():
    """Test that empty bullet lines are ignored."""
    markdown = """- Valid item
- 
- Another valid item"""

    items = extract_lists(markdown)
    assert items == ["Valid item", "Another valid item"]


def test_extract_lists_with_indented_bullets():
    """Test extracting lists with indented bullets."""
    markdown = """  - Indented item
    - More indented
- Not indented"""

    items = extract_lists(markdown)
    # All should be extracted as they start with - or * after stripping
    assert len(items) == 3
    assert "Indented item" in items


def test_split_by_headings_with_empty_input():
    """Test split_by_headings with empty string."""
    result = split_by_headings("", level=2)
    assert result == {"": ""}


def test_extract_lists_with_empty_input():
    """Test extract_lists with empty string."""
    result = extract_lists("")
    assert result == []
