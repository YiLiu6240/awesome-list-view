"""JSON generation pipeline for awesome list data.

This module handles combining multiple awesome list files into a single
JSON cache file according to the specification.
"""

import json
from pathlib import Path

from app.funcs.markdown_parser import parse_awesome_list
from app.funcs.schema import AwesomeList


def apply_exclude_tags_to_lists(
    awesome_lists: list[AwesomeList], exclude_tags: list[str]
) -> list[AwesomeList]:
    """Apply exclude tags filtering to awesome lists.

    Args:
        awesome_lists: List of parsed awesome lists
        exclude_tags: List of tags to exclude

    Returns:
        List of awesome lists with excluded items removed
    """
    if not exclude_tags:
        return awesome_lists

    exclude_tags_set = set(exclude_tags)
    filtered_lists = []

    for awesome_list in awesome_lists:
        # Filter out items that have any excluded tags
        filtered_items = []
        for item in awesome_list["items"]:
            item_tags = set(item["tags"])
            # Include item only if it has no excluded tags
            if not item_tags.intersection(exclude_tags_set):
                filtered_items.append(item)

        # Create new awesome list with filtered items
        filtered_list: AwesomeList = {
            "topic": awesome_list["topic"],
            "items": filtered_items,
            "source_file": awesome_list["source_file"],
        }
        filtered_lists.append(filtered_list)

    return filtered_lists


def generate_awesome_list_json(
    awesome_list_paths: list[str], exclude_tags: list[str] | None = None
) -> str:
    """Generate JSON from multiple awesome list files.

    Args:
        awesome_list_paths: List of paths to markdown files
        exclude_tags: List of tags to exclude from cache generation

    Returns:
        JSON string representation of all awesome lists
    """
    awesome_lists, errors = parse_all_files(awesome_list_paths)

    # Apply exclude tags filtering if provided
    if exclude_tags:
        awesome_lists = apply_exclude_tags_to_lists(awesome_lists, exclude_tags)

    # Validate parsed data
    validation_errors = validate_parsed_data(awesome_lists)

    if validation_errors:
        print("Validation warnings:")
        for error in validation_errors:
            print(f"  - {error}")

    if errors:
        print("Parse errors:")
        for error in errors:
            print(f"  - {error}")

    # Extract metadata for filtering
    all_topics = sorted(
        {awesome_list["topic"] for awesome_list in awesome_lists}
    )
    all_tags = set()
    for awesome_list in awesome_lists:
        for item in awesome_list["items"]:
            all_tags.update(item["tags"])
    all_tags = sorted(all_tags)

    # Convert to the expected format with metadata
    json_data = {
        "metadata": {
            "topics": sorted(all_topics),
            "tags": all_tags,
            "total_items": sum(
                len(awesome_list["items"]) for awesome_list in awesome_lists
            ),
            "total_lists": len(awesome_lists),
        },
        "lists": [
            {
                "topic": awesome_list["topic"],
                "items": [
                    {
                        "title": item["title"],
                        "tags": item["tags"],
                        "link": item["link"],
                        "description": item["description"],
                        "sections": item["sections"],
                        "topic": awesome_list[
                            "topic"
                        ],  # Add topic to each item
                        "source_file": item["source_file"],
                        "line_number": item["line_number"],
                    }
                    for item in awesome_list["items"]
                ],
                "source_file": awesome_list["source_file"],
            }
            for awesome_list in awesome_lists
        ],
    }

    return json.dumps(json_data, indent=2, ensure_ascii=False)


def parse_all_files(
    file_paths: list[str],
) -> tuple[list[AwesomeList], list[str]]:
    """Parse multiple awesome list files with error handling.

    Args:
        file_paths: List of file paths to parse

    Returns:
        Tuple of (successful_parses, error_messages)
    """
    awesome_lists = []
    errors = []

    for file_path in file_paths:
        try:
            if not Path(file_path).exists():
                errors.append(f"File not found: {file_path}")
                continue

            awesome_list = parse_awesome_list(file_path)
            awesome_lists.append(awesome_list)

        except Exception as e:
            errors.append(f"Error parsing {file_path}: {str(e)}")

    return awesome_lists, errors


def validate_parsed_data(awesome_lists: list[AwesomeList]) -> list[str]:
    """Validate parsed data for consistency and completeness.

    Args:
        awesome_lists: List of parsed awesome lists

    Returns:
        List of validation warning messages
    """
    warnings = []

    for awesome_list in awesome_lists:
        # Check for required fields
        if not awesome_list.get("topic"):
            warnings.append(
                f"Missing topic in {awesome_list.get('source_file', 'unknown')}"
            )

        if not awesome_list.get("items"):
            warnings.append(
                f"No items found in {awesome_list.get('source_file', 'unknown')}"
            )

        # Check items
        for i, item in enumerate(awesome_list.get("items", [])):
            item_ref = (
                f"item {i + 1} in {awesome_list.get('source_file', 'unknown')}"
            )

            if not item.get("title"):
                warnings.append(f"Missing title for {item_ref}")

            if not item.get("link"):
                warnings.append(f"Missing link for {item_ref}")

            # Check tag validity
            tags = item.get("tags", [])
            if not isinstance(tags, list):
                warnings.append(f"Invalid tags format for {item_ref}")

    return warnings


def write_cache_file(json_data: str, output_path: str) -> None:
    """Write JSON data to cache file.

    Args:
        json_data: JSON string to write
        output_path: Path to output file
    """
    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        f.write(json_data)
