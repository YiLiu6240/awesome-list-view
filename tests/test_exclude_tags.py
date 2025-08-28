"""Tests for exclude tag functionality.

This module tests the exclude_tags feature that filters out items
containing specified tags from curation.
"""

from app.funcs.filter_manager import FilterManager
from app.funcs.schema import AwesomeListItem
from app.funcs.settings_loader import get_exclude_tags


def test_filter_manager_with_empty_exclude_tags():
    """Test FilterManager with empty exclude_tags list."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Test Item 1",
            "link": "https://example.com/1",
            "description": "A test item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Test Item 2",
            "link": "https://example.com/2",
            "description": "Another test item",
            "tags": ["javascript", "frontend"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
    ]

    # Test with empty exclude_tags
    filter_manager = FilterManager(sample_items, [])
    filtered_items = filter_manager.get_filtered_items()

    assert len(filtered_items) == 2
    assert filtered_items == sample_items


def test_filter_manager_with_none_exclude_tags():
    """Test FilterManager with None exclude_tags (should default to empty)."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Test Item 1",
            "link": "https://example.com/1",
            "description": "A test item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
    ]

    # Test with None exclude_tags
    filter_manager = FilterManager(sample_items, None)
    filtered_items = filter_manager.get_filtered_items()

    assert len(filtered_items) == 1
    assert filtered_items == sample_items


def test_exclude_single_tag():
    """Test excluding items with a single tag."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Python Item",
            "link": "https://example.com/python",
            "description": "A Python item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "JavaScript Item",
            "link": "https://example.com/js",
            "description": "A JavaScript item",
            "tags": ["javascript", "frontend"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "Deprecated Item",
            "link": "https://example.com/deprecated",
            "description": "A deprecated item",
            "tags": ["deprecated", "old"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 3,
        },
    ]

    # Exclude items with "deprecated" tag
    filter_manager = FilterManager(sample_items, ["deprecated"])
    filtered_items = filter_manager.get_filtered_items()

    assert len(filtered_items) == 2
    # Should only contain Python and JavaScript items
    titles = [item["title"] for item in filtered_items]
    assert "Python Item" in titles
    assert "JavaScript Item" in titles
    assert "Deprecated Item" not in titles


def test_exclude_multiple_tags():
    """Test excluding items with multiple tags."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Good Item",
            "link": "https://example.com/good",
            "description": "A good item",
            "tags": ["python", "stable"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Deprecated Item",
            "link": "https://example.com/deprecated",
            "description": "A deprecated item",
            "tags": ["deprecated", "old"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "Experimental Item",
            "link": "https://example.com/experimental",
            "description": "An experimental item",
            "tags": ["experimental", "beta"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 3,
        },
        {
            "title": "Beta Item",
            "link": "https://example.com/beta",
            "description": "A beta item",
            "tags": ["beta", "testing"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 4,
        },
    ]

    # Exclude items with "deprecated" or "experimental" tags
    filter_manager = FilterManager(sample_items, ["deprecated", "experimental"])
    filtered_items = filter_manager.get_filtered_items()

    assert len(filtered_items) == 2
    # Should only contain Good Item and Beta Item
    titles = [item["title"] for item in filtered_items]
    assert "Good Item" in titles
    assert "Beta Item" in titles
    assert "Deprecated Item" not in titles
    assert "Experimental Item" not in titles


def test_exclude_tags_with_inheritance():
    """Test exclude tags with tag inheritance from sections/topics."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Item with Inherited Tags",
            "link": "https://example.com/inherited",
            "description": "Item that inherits tags",
            "tags": [
                "python",
                "legacy",
                "framework",
            ],  # "legacy" will be excluded
            "sections": ["Web Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Clean Item",
            "link": "https://example.com/clean",
            "description": "Clean item without excluded tags",
            "tags": ["python", "modern", "framework"],
            "sections": ["Web Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
    ]

    # Exclude items with "legacy" tag
    filter_manager = FilterManager(sample_items, ["legacy"])
    filtered_items = filter_manager.get_filtered_items()

    assert len(filtered_items) == 1
    assert filtered_items[0]["title"] == "Clean Item"


def test_exclude_tags_counts():
    """Test that exclude tag filtering affects tag and topic counts."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Python Item",
            "link": "https://example.com/python",
            "description": "A Python item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Deprecated Python Item",
            "link": "https://example.com/deprecated-python",
            "description": "A deprecated Python item",
            "tags": ["python", "deprecated"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "JavaScript Item",
            "link": "https://example.com/js",
            "description": "A JavaScript item",
            "tags": ["javascript", "web"],
            "sections": ["Development"],
            "topic": "Frontend",
            "source_file": "test.md",
            "line_number": 3,
        },
    ]

    # Exclude items with "deprecated" tag
    filter_manager = FilterManager(sample_items, ["deprecated"])

    # Check tag counts (should not include deprecated item)
    tag_counts = filter_manager.get_tag_counts()
    assert tag_counts["python"] == 1  # Only non-deprecated Python item
    assert tag_counts["web"] == 2  # Both non-deprecated items
    assert tag_counts["javascript"] == 1
    assert "deprecated" not in tag_counts  # Excluded tag should not appear

    # Check topic counts
    topic_counts = filter_manager.get_topic_counts()
    assert topic_counts["Programming"] == 1  # Only non-deprecated Python item
    assert topic_counts["Frontend"] == 1


def test_get_exclude_tags_methods():
    """Test FilterManager methods for managing exclude tags."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Test Item",
            "link": "https://example.com/test",
            "description": "A test item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
    ]

    # Test initial exclude tags
    filter_manager = FilterManager(sample_items, ["deprecated", "legacy"])
    exclude_tags = filter_manager.get_exclude_tags()
    assert exclude_tags == {"deprecated", "legacy"}


def test_set_exclude_tags():
    """Test updating exclude tags dynamically."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Python Item",
            "link": "https://example.com/python",
            "description": "A Python item",
            "tags": ["python", "web"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Deprecated Item",
            "link": "https://example.com/deprecated",
            "description": "A deprecated item",
            "tags": ["deprecated", "old"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "Legacy Item",
            "link": "https://example.com/legacy",
            "description": "A legacy item",
            "tags": ["legacy", "old"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 3,
        },
    ]

    # Start with no exclusions
    filter_manager = FilterManager(sample_items, [])
    assert len(filter_manager.get_filtered_items()) == 3

    # Add exclude tags
    filter_manager.set_exclude_tags(["deprecated"])
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 2
    titles = [item["title"] for item in filtered_items]
    assert "Deprecated Item" not in titles

    # Change exclude tags
    filter_manager.set_exclude_tags(["legacy"])
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 2
    titles = [item["title"] for item in filtered_items]
    assert "Legacy Item" not in titles
    assert "Deprecated Item" in titles  # Should now be included

    # Clear exclude tags
    filter_manager.set_exclude_tags([])
    assert len(filter_manager.get_filtered_items()) == 3


def test_exclude_tags_with_existing_filters():
    """Test exclude tags work correctly with existing tag and topic filters."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Good Python Web Item",
            "link": "https://example.com/good-python",
            "description": "A good Python web item",
            "tags": ["python", "web", "stable"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Deprecated Python Web Item",
            "link": "https://example.com/deprecated-python",
            "description": "A deprecated Python web item",
            "tags": ["python", "web", "deprecated"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "Good JavaScript Web Item",
            "link": "https://example.com/good-js",
            "description": "A good JavaScript web item",
            "tags": ["javascript", "web", "modern"],
            "sections": ["Development"],
            "topic": "Frontend",
            "source_file": "test.md",
            "line_number": 3,
        },
    ]

    # Exclude deprecated items
    filter_manager = FilterManager(sample_items, ["deprecated"])

    # Should have 2 items initially (excluding deprecated)
    assert len(filter_manager.get_filtered_items()) == 2

    # Apply tag filter for "web"
    filter_manager.add_tag_filter("web")
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 2  # Both remaining items have "web" tag

    # Apply topic filter for "Programming"
    filter_manager.add_topic_filter("Programming")
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 1  # Only the good Python item
    assert filtered_items[0]["title"] == "Good Python Web Item"


def test_exclude_tags_counts_total_and_excluded():
    """Test methods for getting total and excluded item counts."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Item 1",
            "link": "https://example.com/1",
            "description": "Good item",
            "tags": ["good"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Item 2",
            "link": "https://example.com/2",
            "description": "Deprecated item",
            "tags": ["deprecated"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
        {
            "title": "Item 3",
            "link": "https://example.com/3",
            "description": "Legacy item",
            "tags": ["legacy"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 3,
        },
    ]

    # Exclude deprecated and legacy items
    filter_manager = FilterManager(sample_items, ["deprecated", "legacy"])

    assert filter_manager.get_total_items_count() == 3  # Original total
    assert filter_manager.get_excluded_items_count() == 2  # Excluded count
    assert (
        len(filter_manager.get_filtered_items()) == 1
    )  # Available after exclusion


def test_get_exclude_tags_from_settings(tmp_path):
    """Test loading exclude_tags from settings."""
    # This test requires a mock or fixture for settings
    # For now, test that get_exclude_tags returns empty list when no config
    exclude_tags = get_exclude_tags("nonexistent_path.toml")
    assert exclude_tags == []


def test_exclude_tags_validation():
    """Test that exclude_tags validation works correctly."""
    from app.funcs.settings_loader import validate_settings

    # This will test the validation logic we added
    # Should not raise errors for missing exclude_tags (optional setting)
    errors = validate_settings("nonexistent_path.toml")
    # Should contain file not found error but not exclude_tags validation error
    assert any("configuration file" in error.lower() for error in errors)

    # No exclude_tags specific errors should be present for missing file
    assert not any("EXCLUDE_TAGS" in error for error in errors)


def test_empty_tags_not_affected_by_exclude():
    """Test that items with empty tags are not affected by exclude filtering."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Item with Tags",
            "link": "https://example.com/tagged",
            "description": "Item with tags",
            "tags": ["python", "deprecated"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Item without Tags",
            "link": "https://example.com/untagged",
            "description": "Item without tags",
            "tags": [],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
    ]

    # Exclude deprecated items
    filter_manager = FilterManager(sample_items, ["deprecated"])
    filtered_items = filter_manager.get_filtered_items()

    # Should only have the untagged item
    assert len(filtered_items) == 1
    assert filtered_items[0]["title"] == "Item without Tags"


def test_case_sensitive_exclude_tags():
    """Test that exclude tag filtering is case-sensitive."""
    sample_items: list[AwesomeListItem] = [
        {
            "title": "Item with lowercase tag",
            "link": "https://example.com/lower",
            "description": "Item with lowercase deprecated tag",
            "tags": ["deprecated"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 1,
        },
        {
            "title": "Item with uppercase tag",
            "link": "https://example.com/upper",
            "description": "Item with uppercase deprecated tag",
            "tags": ["DEPRECATED"],
            "sections": ["Development"],
            "topic": "Programming",
            "source_file": "test.md",
            "line_number": 2,
        },
    ]

    # Exclude only lowercase "deprecated"
    filter_manager = FilterManager(sample_items, ["deprecated"])
    filtered_items = filter_manager.get_filtered_items()

    # Should only exclude the lowercase version
    assert len(filtered_items) == 1
    assert filtered_items[0]["title"] == "Item with uppercase tag"
