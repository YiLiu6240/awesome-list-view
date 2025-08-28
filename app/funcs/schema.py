"""Data schemas for awesome-list-view using TypedDict for type safety.

This module defines the core data structures used throughout the application
for parsing markdown files and generating JSON cache.
"""

from typing import Any, TypedDict


class AwesomeListItem(TypedDict):
    """Represents a single item in an awesome list.

    Attributes:
        title: The title/name of the item (first line of bullet point)
        link: The primary URL for the item (first URL found)
        description: Additional description text for the item
        tags: List of tags (inherited from frontmatter/headings + inline)
        sections: List of heading hierarchy (level-2 and level-3 ancestors)
        topic: The topic this item belongs to (from level-1 heading)
        source_file: Path to the source markdown file
        line_number: Line number where this item appears in the source file
    """

    title: str
    link: str
    description: str
    tags: list[str]
    sections: list[str]
    topic: str
    source_file: str
    line_number: int


class AwesomeList(TypedDict):
    """Represents a complete awesome list from a markdown file.

    Attributes:
        topic: The topic from the level-1 heading
        items: List of all items found in the file
        source_file: Path to the source markdown file
    """

    topic: str
    items: list[AwesomeListItem]
    source_file: str


class ParsedMarkdown(TypedDict):
    """Intermediate data structure during markdown parsing.

    Attributes:
        frontmatter_tags: Tags extracted from YAML frontmatter
        topic: The main topic from level-1 heading
        sections: Hierarchical structure of headings with metadata
    """

    frontmatter_tags: list[str]
    topic: str
    sections: dict[str, Any]


class FileMetadata(TypedDict):
    """Metadata about parsed markdown files.

    Attributes:
        file_path: Absolute path to the markdown file
        last_modified: Unix timestamp of last modification
        parse_errors: List of error messages encountered during parsing
    """

    file_path: str
    last_modified: float
    parse_errors: list[str]


class CacheMetadata(TypedDict):
    """Metadata about the cache file for filtering and statistics.

    Attributes:
        topics: List of all available topics
        tags: List of all available tags
        total_items: Total number of items across all lists
        total_lists: Total number of awesome lists
    """

    topics: list[str]
    tags: list[str]
    total_items: int
    total_lists: int


class CacheData(TypedDict):
    """Complete cache data structure with metadata and lists.

    Attributes:
        metadata: Metadata for filtering and statistics
        lists: List of all awesome lists with items
    """

    metadata: CacheMetadata
    lists: list[AwesomeList]


class HeadingInfo(TypedDict):
    """Information about a markdown heading.

    Attributes:
        level: Heading level (1-6)
        text: Raw heading text with tags
        clean_text: Heading text with tags removed
        tags: List of inline tags extracted from heading
        line_number: Line number where heading appears
    """

    level: int
    text: str
    clean_text: str
    tags: list[str]
    line_number: int
