# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Markdown normalizer for user story sections.

This module handles parsing markdown content and normalizing headings to canonical section names.
"""

from living_doc_core.markdown_utils import (  # type: ignore[import-untyped]
    normalize_heading,
    split_by_headings,
)

# Heading synonym mapping (case-insensitive)
HEADING_SYNONYMS = {
    "description": ["description", "overview", "summary"],
    "business_value": ["business value", "value", "why"],
    "preconditions": ["preconditions", "prerequisites", "setup"],
    "acceptance_criteria": ["acceptance criteria", "ac", "done criteria"],
    "user_guide": ["user guide", "how to", "instructions"],
    "connections": ["connections", "related", "links"],
    "last_edited": ["last edited", "history", "changes"],
}


def normalize_sections(markdown: str) -> dict:  # pylint: disable=too-many-branches
    """
    Normalize markdown content into canonical sections.

    This function parses markdown by H2 headings and maps them to canonical section names
    using synonym mapping. Unknown headings are appended to the description section.
    Content before the first heading is assigned to description.

    Args:
        markdown: The markdown text to normalize

    Returns:
        Dictionary with canonical section keys (description, business_value, etc.)
        and their markdown content. Sections without content are omitted.
    """
    if not markdown:
        return {"description": None}

    # Split markdown by H2 headings
    sections_raw = split_by_headings(markdown, level=2)

    # Build reverse lookup map for synonyms
    synonym_to_canonical = {}
    for canonical, synonyms in HEADING_SYNONYMS.items():
        for synonym in synonyms:
            synonym_to_canonical[synonym] = canonical

    # Initialize result with canonical section keys
    result = {}

    # Track description content (for unknown headings and pre-heading content)
    description_parts = []

    # Process content before first heading
    if "" in sections_raw and sections_raw[""]:
        description_parts.append(sections_raw[""].strip())

    # First pass: collect known sections and track description synonym
    known_description_content = None

    # Process each heading and its content
    for heading, content in sections_raw.items():
        if heading == "":  # Already processed above
            continue

        # Normalize heading to lowercase for synonym matching
        normalized = normalize_heading(heading)

        # Check if heading matches a known synonym
        if normalized in synonym_to_canonical:
            canonical = synonym_to_canonical[normalized]
            # Store content under canonical section key
            if content and content.strip():
                if canonical == "description":
                    # Store description content to prepend to description_parts
                    known_description_content = content.strip()
                else:
                    result[canonical] = content.strip()
        else:
            # Unknown heading: append to description as structured content
            if content and content.strip():
                description_parts.append(f"### {heading}\n{content.strip()}")

    # Build final description by combining known description + pre-heading + unknown
    final_description_parts = []
    if known_description_content:
        final_description_parts.append(known_description_content)
    if description_parts:
        final_description_parts.extend(description_parts)

    if final_description_parts:
        result["description"] = "\n\n".join(final_description_parts)

    # Ensure empty sections are represented as None
    if not result:
        result["description"] = None

    return result
