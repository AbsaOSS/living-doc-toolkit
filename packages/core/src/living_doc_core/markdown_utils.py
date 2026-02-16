# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Markdown utilities for parsing and normalizing markdown text.
"""

import re


def split_by_headings(markdown_text: str, level: int = 2) -> dict[str, str]:
    """
    Split markdown text by headings of a given level.

    Args:
        markdown_text: The markdown text to split
        level: The heading level to split by (default: 2 for H2 = ##)

    Returns:
        Dictionary mapping heading text to content under that heading.
        Content before the first heading is keyed as "" (empty string).
    """
    if not markdown_text:
        return {"": ""}

    # Create pattern for headings of the specified level
    # Match lines starting with exact number of # followed by space
    heading_pattern = re.compile(r"^#{" + str(level) + r"}\s+(.+)$", re.MULTILINE)

    # Find all heading matches with their positions
    matches = list(heading_pattern.finditer(markdown_text))

    if not matches:
        # No headings found, return all content under empty key
        return {"": markdown_text}

    result = {}

    # Handle content before first heading
    first_heading_pos = matches[0].start()
    if first_heading_pos > 0:
        pre_content = markdown_text[:first_heading_pos].rstrip()
        result[""] = pre_content

    # Process each heading and its content
    for i, match in enumerate(matches):
        heading_text = match.group(1).strip()

        # Find where content starts (after the heading line)
        content_start = match.end()
        if content_start < len(markdown_text) and markdown_text[content_start] == "\n":
            content_start += 1

        # Find where content ends (at next heading or end of text)
        if i + 1 < len(matches):
            content_end = matches[i + 1].start()
        else:
            content_end = len(markdown_text)

        # Extract and strip content
        content = markdown_text[content_start:content_end].rstrip()
        result[heading_text] = content

    return result


def normalize_heading(text: str) -> str:
    """
    Normalize a heading by converting to lowercase and stripping whitespace.

    Args:
        text: The heading text to normalize

    Returns:
        Normalized heading text (lowercase, stripped)
    """
    return text.strip().lower()


def extract_lists(markdown_text: str) -> list[str]:
    """
    Extract bullet list items from markdown text.

    Args:
        markdown_text: The markdown text to parse

    Returns:
        List of bullet point items (lines starting with "- " or "* ")
    """
    if not markdown_text:
        return []

    lines = markdown_text.split("\n")
    items = []

    for line in lines:
        stripped = line.strip()
        # Match lines starting with - or * followed by space
        if stripped.startswith("- ") or stripped.startswith("* "):
            # Remove the bullet marker and leading space
            item_text = stripped[2:].strip()
            if item_text:
                items.append(item_text)

    return items
