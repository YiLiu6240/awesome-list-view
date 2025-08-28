"""Tag processing and inheritance system for awesome lists.

This module handles the complex logic of tag inheritance from frontmatter,
headings, and inline tags according to the specification.
"""

from typing import Any


def inherit_tags(
    item: dict[str, Any], section_tags: list[str], frontmatter_tags: list[str]
) -> list[str]:
    """Combine item tags with inherited tags from sections and frontmatter.

    Args:
        item: Item dictionary containing inline tags
        section_tags: Tags from ancestor headings
        frontmatter_tags: Tags from YAML frontmatter

    Returns:
        List of all inherited tags (deduplicated, preserving order)
    """
    # Get inline tags from item
    inline_tags = item.get("tags", [])

    # Combine in order: inline, section, frontmatter
    all_tags = []

    # Add inline tags first
    for tag in inline_tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in all_tags:
            all_tags.append(normalized)

    # Add section tags
    for tag in section_tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in all_tags:
            all_tags.append(normalized)

    # Add frontmatter tags
    for tag in frontmatter_tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in all_tags:
            all_tags.append(normalized)

    # Filter out excluded tags
    return filter_meaningful_tags(all_tags)


def filter_meaningful_tags(tags: list[str]) -> list[str]:
    """Remove excluded tags like 'awesome' that are not meaningful.

    Args:
        tags: List of tag strings

    Returns:
        Filtered list with excluded tags removed
    """
    excluded_tags = {"awesome"}
    return [tag for tag in tags if tag.lower() not in excluded_tags]


def normalize_tag(tag: str) -> str:
    """Normalize a tag string for consistency.

    Args:
        tag: Raw tag string

    Returns:
        Normalized tag (lowercase, stripped, with special chars handled)
    """
    if not tag:
        return ""

    # Remove leading/trailing whitespace
    normalized = tag.strip()

    # Convert to lowercase for consistency
    normalized = normalized.lower()

    # Remove any leading # if present
    if normalized.startswith("#"):
        normalized = normalized[1:]

    # Replace spaces and other characters with hyphens
    import re

    normalized = re.sub(r"[^\w-]", "-", normalized)

    # Remove multiple consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized)

    # Remove leading/trailing hyphens
    normalized = normalized.strip("-")

    return normalized


def get_ancestor_tags(
    heading_hierarchy: list[dict[str, Any]], item_position: int
) -> list[str]:
    """Extract tags from ancestor headings for tag inheritance.

    Args:
        heading_hierarchy: List of heading information
        item_position: Line number or position of the item

    Returns:
        List of tags from all ancestor headings
    """
    ancestor_tags = []

    # Find all headings that come before this item
    relevant_headings = []
    for heading in heading_hierarchy:
        if heading.get("line_number", 0) < item_position:
            relevant_headings.append(heading)

    if not relevant_headings:
        return []

    # Find the most recent heading at each level
    current_headings = {}
    for heading in relevant_headings:
        level = heading.get("level", 1)
        # Clear deeper levels when we encounter a shallower heading
        levels_to_clear = [
            level_key
            for level_key in current_headings.keys()
            if level_key >= level
        ]
        for level_key in levels_to_clear:
            del current_headings[level_key]
        current_headings[level] = heading

    # Collect tags from current heading hierarchy (level 2 and 3 only per spec)
    for level in sorted(current_headings.keys()):
        if level >= 2:  # Only H2 and deeper contribute to sections
            heading = current_headings[level]
            heading_tags = heading.get("tags", [])
            for tag in heading_tags:
                normalized = normalize_tag(tag)
                if normalized and normalized not in ancestor_tags:
                    ancestor_tags.append(normalized)

    return ancestor_tags


def build_section_names(
    heading_hierarchy: list[dict[str, Any]], item_position: int
) -> list[str]:
    """Build section name hierarchy for an item.

    Args:
        heading_hierarchy: List of heading information
        item_position: Line number or position of the item

    Returns:
        List of section names (H2 and H3 ancestors)
    """
    # Find relevant headings before this item
    relevant_headings = []
    for heading in heading_hierarchy:
        if heading.get("line_number", 0) < item_position:
            relevant_headings.append(heading)

    if not relevant_headings:
        return []

    # Find current heading at each level
    current_headings = {}
    for heading in relevant_headings:
        level = heading.get("level", 1)
        # Clear deeper levels when we encounter a shallower heading
        levels_to_clear = [
            level_key
            for level_key in current_headings.keys()
            if level_key >= level
        ]
        for level_key in levels_to_clear:
            del current_headings[level_key]
        current_headings[level] = heading

    # Build section names (H2 and H3 only per spec)
    sections = []
    for level in sorted(current_headings.keys()):
        if level >= 2:  # Only H2 and deeper are sections
            heading = current_headings[level]
            clean_text = heading.get("clean_text", heading.get("text", ""))
            if clean_text:
                sections.append(clean_text)

    return sections
