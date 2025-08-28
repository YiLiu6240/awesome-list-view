"""Markdown parser for awesome list files.

This module provides functions to parse markdown files according to the
awesome-list-view specification, extracting frontmatter, headings, and
list items with proper tag inheritance.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from app.funcs.schema import (
    AwesomeList,
    AwesomeListItem,
    HeadingInfo,
)
from app.funcs.tag_processor import (
    build_section_names,
    get_ancestor_tags,
    inherit_tags,
)


def parse_awesome_list(file_path: str) -> AwesomeList:
    """Parse an awesome list markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        AwesomeList object with parsed data

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Awesome list file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise PermissionError(f"Cannot read file {file_path}: {e}") from e

    return parse_markdown_content(content, file_path)


def parse_markdown_content(content: str, file_path: str) -> AwesomeList:
    """Parse markdown content into an AwesomeList structure.

    Args:
        content: Raw markdown content
        file_path: Path to source file (for metadata)

    Returns:
        AwesomeList object with all parsed data
    """
    # Parse frontmatter
    frontmatter, content_without_frontmatter = parse_frontmatter(content)
    frontmatter_tags = frontmatter.get("tags", [])

    # Extract headings
    headings = extract_headings(content_without_frontmatter)

    # Find topic (first H1 heading)
    topic = ""
    for heading in headings:
        if heading["level"] == 1:
            topic = heading["clean_text"]
            break

    if not topic:
        raise ValueError(f"No H1 heading found in {file_path}")

    # Extract list items
    raw_items = extract_list_items(content_without_frontmatter, headings)

    # Process items with tag inheritance
    processed_items = []
    for raw_item in raw_items:
        processed_item = process_item(
            raw_item, headings, frontmatter_tags, topic, file_path
        )
        if processed_item:
            processed_items.append(processed_item)

    awesome_list: AwesomeList = {
        "topic": topic,
        "items": processed_items,
        "source_file": file_path,
    }

    return awesome_list


def process_item(
    raw_item: dict[str, Any],
    headings: list[HeadingInfo],
    frontmatter_tags: list[str],
    topic: str,
    source_file: str,
) -> AwesomeListItem | None:
    """Process a raw item into an AwesomeListItem with tag inheritance.

    Args:
        raw_item: Raw item data from extraction
        headings: All headings for context
        frontmatter_tags: Tags from frontmatter
        topic: The topic this item belongs to
        source_file: Path to the source file

    Returns:
        Processed AwesomeListItem or None if item is invalid
    """
    # Parse item content
    raw_text = raw_item.get("raw_text", [])
    full_text = (
        " ".join(raw_text) if isinstance(raw_text, list) else str(raw_text)
    )

    title, description, link, inline_tags = parse_item_content(full_text)

    if not title.strip():
        return None  # Skip items without titles

    # Get position for context
    item_position = raw_item.get("line_number", 0)

    # Get ancestor tags and sections
    headings_as_dicts = [dict(heading) for heading in headings]
    ancestor_tags = get_ancestor_tags(headings_as_dicts, item_position)
    sections = build_section_names(headings_as_dicts, item_position)

    # Create item dict for tag inheritance
    item_dict = {"tags": inline_tags}

    # Apply tag inheritance
    all_tags = inherit_tags(item_dict, ancestor_tags, frontmatter_tags)

    awesome_item: AwesomeListItem = {
        "title": title.strip(),
        "link": link,
        "description": description.strip(),
        "tags": all_tags,
        "sections": sections,
        "topic": topic,
        "source_file": source_file,
        "line_number": item_position,
    }

    return awesome_item


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content.

    Args:
        content: Raw markdown content

    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    # Match YAML frontmatter delimited by ---
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return {}, content

    yaml_content = match.group(1)
    remaining_content = content[match.end() :]

    try:
        frontmatter = yaml.safe_load(yaml_content) or {}
        return frontmatter, remaining_content
    except yaml.YAMLError:
        # Return empty dict if YAML is malformed
        return {}, content


def extract_headings(content: str) -> list[HeadingInfo]:
    """Extract all headings from markdown content.

    Args:
        content: Markdown content without frontmatter

    Returns:
        List of HeadingInfo objects for each heading found
    """
    headings = []
    lines = content.split("\n")

    # Pattern to match markdown headings (1-6 levels)
    heading_pattern = r"^(#{1,6})\s+(.+)$"

    for line_num, line in enumerate(lines, 1):
        match = re.match(heading_pattern, line.strip())
        if match:
            hashes, text = match.groups()
            level = len(hashes)
            clean_text, tags = parse_heading_tags(text)

            heading_info: HeadingInfo = {
                "level": level,
                "text": text,
                "clean_text": clean_text,
                "tags": tags,
                "line_number": line_num,
            }
            headings.append(heading_info)

    return headings


def parse_heading_tags(heading_text: str) -> tuple[str, list[str]]:
    """Extract inline tags from heading text.

    Args:
        heading_text: Raw heading text potentially containing #tags

    Returns:
        Tuple of (clean_text, tags_list)
    """
    # Pattern to find #tags (hashtag followed by word characters)
    tag_pattern = r"#([a-zA-Z0-9_-]+)"

    # Find all tags
    tags = re.findall(tag_pattern, heading_text)

    # Remove tags from text to get clean version
    clean_text = re.sub(tag_pattern, "", heading_text).strip()
    # Clean up extra whitespace
    clean_text = re.sub(r"\s+", " ", clean_text)

    return clean_text, tags


def extract_list_items(
    content: str, headings: list[HeadingInfo]
) -> list[dict[str, Any]]:
    """Extract bullet point items and associate with headings.

    Args:
        content: Markdown content
        headings: List of parsed headings for context

    Returns:
        List of dictionaries containing item data and context
    """
    items = []
    lines = content.split("\n")
    current_item = None
    current_context = {"headings": []}

    # Build heading context map (line number -> heading info)
    heading_map = {h["line_number"]: h for h in headings}

    for line_num, line in enumerate(lines, 1):
        # Update context based on headings
        if line_num in heading_map:
            current_context = build_heading_context(
                heading_map[line_num], headings
            )

        # Check for bullet point items
        bullet_match = re.match(r"^[\s]*[-*]\s+(.+)$", line)
        if bullet_match:
            # Save previous item if exists
            if current_item:
                items.append(current_item)

            # Start new item
            item_text = bullet_match.group(1)
            current_item = {
                "raw_text": [item_text],
                "context": current_context.copy(),
                "line_number": line_num,
            }
        elif current_item and line.strip():
            # Continue current item with additional content
            # Check if line is indented (part of current item)
            if line.startswith("  ") or line.startswith("\t"):
                current_item["raw_text"].append(line.strip())
        elif current_item and not line.strip():
            # Empty line might end item, but we'll be lenient
            pass

    # Don't forget the last item
    if current_item:
        items.append(current_item)

    return items


def build_heading_context(
    current_heading: HeadingInfo, all_headings: list[HeadingInfo]
) -> dict[str, Any]:
    """Build hierarchical context for the current position.

    Args:
        current_heading: The heading we just encountered
        all_headings: All headings in the document

    Returns:
        Context dictionary with heading hierarchy
    """
    # Find the hierarchical path to this heading
    context_headings = []

    # For now, simplified: just include current heading
    # In a full implementation, we'd build the complete hierarchy
    context_headings.append(current_heading)

    return {"headings": context_headings}


def parse_item_content(item_text: str) -> tuple[str, str, str, list[str]]:
    """Parse individual item text to extract components.

    Args:
        item_text: Raw text from bullet point (may be multi-line)

    Returns:
        Tuple of (title, description, link, tags)
    """
    # Join multi-line text
    if isinstance(item_text, list):
        full_text = " ".join(item_text)
    else:
        full_text = item_text

    # Extract URLs first
    urls = extract_urls(full_text)
    link = urls[0] if urls else ""

    # Remove URLs from text for further processing
    text_without_urls = full_text
    for url in urls:
        text_without_urls = text_without_urls.replace(url, "").replace("<>", "")

    # Extract tags
    tag_pattern = r"#([a-zA-Z0-9_-]+)"
    tags = re.findall(tag_pattern, text_without_urls)

    # Remove tags from text
    text_without_tags = re.sub(tag_pattern, "", text_without_urls)

    # Clean up text
    text_parts = [
        part.strip() for part in text_without_tags.split("\n") if part.strip()
    ]

    if not text_parts:
        return "", "", link, tags

    # First part is title, rest is description
    title = text_parts[0]
    description = " ".join(text_parts[1:]) if len(text_parts) > 1 else ""

    return title, description, link, tags


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text in various formats.

    Args:
        text: Text that may contain URLs

    Returns:
        List of URLs found
    """
    urls = []

    # Pattern for URLs in angle brackets: <http://example.com>
    angle_pattern = r"<(https?://[^\s>]+)>"
    urls.extend(re.findall(angle_pattern, text))

    # Pattern for bare URLs: http://example.com
    bare_pattern = r"(?<!<)(https?://[^\s<>]+)(?![>])"
    urls.extend(re.findall(bare_pattern, text))

    # Pattern for markdown links: [text](url)
    markdown_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    markdown_matches = re.findall(markdown_pattern, text)
    urls.extend([match[1] for match in markdown_matches])

    return urls
