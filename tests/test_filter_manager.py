"""Unit tests for the filter manager module."""

import pytest

from app.funcs.filter_manager import FilterManager, FilterMode
from app.funcs.schema import AwesomeListItem


@pytest.fixture
def sample_items() -> list[AwesomeListItem]:
    """Create sample awesome list items for testing."""
    return [
        {
            "title": "Python Library",
            "link": "https://python.org",
            "description": "A Python library for testing",
            "tags": ["python", "library", "testing"],
            "sections": ["Development", "Libraries"],
            "topic": "Programming Languages",
        },
        {
            "title": "JavaScript Framework",
            "link": "https://javascript.com",
            "description": "A JS framework for web development",
            "tags": ["javascript", "framework", "web"],
            "sections": ["Web Development", "Frameworks"],
            "topic": "Web Development",
        },
        {
            "title": "Python Web Framework",
            "link": "https://flask.dev",
            "description": "A lightweight Python web framework",
            "tags": ["python", "web", "framework"],
            "sections": ["Web Development", "Python"],
            "topic": "Web Development",
        },
        {
            "title": "Testing Tool",
            "link": "https://pytest.org",
            "description": "A testing framework for Python",
            "tags": ["testing", "python", "framework"],
            "sections": ["Development", "Testing"],
            "topic": "Programming Languages",
        },
        {
            "title": "Documentation Generator",
            "link": "https://docs.com",
            "description": "Generate documentation automatically",
            "tags": ["documentation", "generator"],
            "sections": ["Documentation", "Tools"],
            "topic": "Developer Tools",
        },
    ]


def test_filter_manager_initialization(sample_items):
    """Test FilterManager initialization."""
    filter_manager = FilterManager(sample_items)

    assert len(filter_manager._items) == 5
    assert filter_manager.get_filter_mode() == FilterMode.OR
    assert len(filter_manager.get_selected_tags()) == 0
    assert len(filter_manager.get_selected_topics()) == 0
    assert len(filter_manager.get_filtered_items()) == 5


def test_tag_counts_calculation(sample_items):
    """Test tag counts are calculated correctly."""
    filter_manager = FilterManager(sample_items)
    tag_counts = filter_manager.get_tag_counts()

    # Check expected tag counts
    assert tag_counts["python"] == 3
    assert tag_counts["framework"] == 3
    assert tag_counts["testing"] == 2
    assert tag_counts["web"] == 2
    assert tag_counts["javascript"] == 1
    assert tag_counts["library"] == 1
    assert tag_counts["documentation"] == 1
    assert tag_counts["generator"] == 1


def test_available_tags_sorted(sample_items):
    """Test available tags are returned sorted."""
    filter_manager = FilterManager(sample_items)
    tags = filter_manager.get_available_tags()

    assert tags == sorted(tags)
    assert "documentation" in tags
    assert "python" in tags
    assert "web" in tags


def test_add_tag_filter(sample_items):
    """Test adding tag filters."""
    filter_manager = FilterManager(sample_items)

    # Add python tag filter
    filter_manager.add_tag_filter("python")

    assert "python" in filter_manager.get_selected_tags()
    assert len(filter_manager.get_selected_tags()) == 1

    # In OR mode, should return all items with python tag
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 3

    # Check titles of filtered items
    titles = {item["title"] for item in filtered_items}
    expected_titles = {"Python Library", "Python Web Framework", "Testing Tool"}
    assert titles == expected_titles


def test_remove_tag_filter(sample_items):
    """Test removing tag filters."""
    filter_manager = FilterManager(sample_items)

    # Add and then remove a filter
    filter_manager.add_tag_filter("python")
    assert "python" in filter_manager.get_selected_tags()

    filter_manager.remove_tag_filter("python")
    assert "python" not in filter_manager.get_selected_tags()
    assert len(filter_manager.get_filtered_items()) == 5  # Back to all items


def test_toggle_tag_filter(sample_items):
    """Test toggling tag filters."""
    filter_manager = FilterManager(sample_items)

    # Toggle on
    filter_manager.toggle_tag_filter("web")
    assert "web" in filter_manager.get_selected_tags()

    # Toggle off
    filter_manager.toggle_tag_filter("web")
    assert "web" not in filter_manager.get_selected_tags()


def test_clear_filters(sample_items):
    """Test clearing all filters."""
    filter_manager = FilterManager(sample_items)

    # Add multiple filters
    filter_manager.add_tag_filter("python")
    filter_manager.add_tag_filter("web")
    assert len(filter_manager.get_selected_tags()) == 2

    # Clear all
    filter_manager.clear_filters()
    assert len(filter_manager.get_selected_tags()) == 0
    assert len(filter_manager.get_filtered_items()) == 5


def test_filter_mode_and_logic(sample_items):
    """Test AND mode filtering logic."""
    filter_manager = FilterManager(sample_items)

    # Set up AND mode
    filter_manager.set_filter_mode(FilterMode.AND)
    assert filter_manager.get_filter_mode() == FilterMode.AND

    # Add filters for python AND framework
    filter_manager.add_tag_filter("python")
    filter_manager.add_tag_filter("framework")

    # Should only return items that have both tags
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 2  # Python Web Framework and Testing Tool

    titles = {item["title"] for item in filtered_items}
    expected_titles = {"Python Web Framework", "Testing Tool"}
    assert titles == expected_titles


def test_filter_mode_or_logic(sample_items):
    """Test OR mode filtering logic."""
    filter_manager = FilterManager(sample_items)

    # Default mode is OR
    assert filter_manager.get_filter_mode() == FilterMode.OR

    # Add filters for javascript OR documentation
    filter_manager.add_tag_filter("javascript")
    filter_manager.add_tag_filter("documentation")

    # Should return items that have either tag
    filtered_items = filter_manager.get_filtered_items()
    assert (
        len(filtered_items) == 2
    )  # JavaScript Framework and Documentation Generator

    titles = {item["title"] for item in filtered_items}
    expected_titles = {"JavaScript Framework", "Documentation Generator"}
    assert titles == expected_titles


def test_toggle_filter_mode(sample_items):
    """Test toggling between filter modes."""
    filter_manager = FilterManager(sample_items)

    # Start with OR mode
    assert filter_manager.get_filter_mode() == FilterMode.OR

    # Toggle to AND
    filter_manager.toggle_filter_mode()
    assert filter_manager.get_filter_mode() == FilterMode.AND

    # Toggle back to OR
    filter_manager.toggle_filter_mode()
    assert filter_manager.get_filter_mode() == FilterMode.OR


def test_filter_status_messages(sample_items):
    """Test filter status message generation."""
    filter_manager = FilterManager(sample_items)

    # No filters
    status = filter_manager.get_filter_status()
    assert status == "Showing all 5 items"

    # Single filter
    filter_manager.add_tag_filter("python")
    status = filter_manager.get_filter_status()
    assert status == "Showing 3 of 5 items (1 filter active: 1 tag)"

    # Multiple filters (python OR framework = 4 items)
    filter_manager.add_tag_filter("framework")
    status = filter_manager.get_filter_status()
    assert status == "Showing 4 of 5 items (2 filters active: 2 tag)"


def test_has_active_filters(sample_items):
    """Test checking for active filters."""
    filter_manager = FilterManager(sample_items)

    # No filters
    assert not filter_manager.has_active_filters()

    # Add filter
    filter_manager.add_tag_filter("python")
    assert filter_manager.has_active_filters()

    # Clear filters
    filter_manager.clear_filters()
    assert not filter_manager.has_active_filters()


def test_update_items(sample_items):
    """Test updating items and refreshing filters."""
    filter_manager = FilterManager(sample_items)

    # Add a filter
    filter_manager.add_tag_filter("python")
    assert len(filter_manager.get_filtered_items()) == 3

    # Update with new items (subset)
    new_items = sample_items[:2]  # Only first 2 items
    filter_manager.update_items(new_items)

    # Should still have python filter but fewer results
    assert "python" in filter_manager.get_selected_tags()
    assert len(filter_manager.get_filtered_items()) == 1  # Only Python Library

    # Tag counts should be updated
    tag_counts = filter_manager.get_tag_counts()
    assert tag_counts["python"] == 1


def test_filter_summary(sample_items):
    """Test getting filter summary statistics."""
    filter_manager = FilterManager(sample_items)

    # No filters
    total, filtered, active = filter_manager.get_filter_summary()
    assert total == 5
    assert filtered == 5
    assert active == 0

    # With filters (python OR web = 4 items)
    filter_manager.add_tag_filter("python")
    filter_manager.add_tag_filter("web")

    total, filtered, active = filter_manager.get_filter_summary()
    assert total == 5
    assert filtered == 4  # Items with python OR web
    assert active == 2


def test_invalid_tag_handling(sample_items):
    """Test handling of invalid/non-existent tags."""
    filter_manager = FilterManager(sample_items)

    # Try to add non-existent tag
    filter_manager.add_tag_filter("nonexistent")

    # Should not be added to selected tags
    assert "nonexistent" not in filter_manager.get_selected_tags()
    assert len(filter_manager.get_selected_tags()) == 0

    # Try to remove non-existent tag (should not error)
    filter_manager.remove_tag_filter("nonexistent")
    assert len(filter_manager.get_selected_tags()) == 0


def test_empty_items_list():
    """Test FilterManager with empty items list."""
    filter_manager = FilterManager([])

    assert len(filter_manager.get_tag_counts()) == 0
    assert len(filter_manager.get_available_tags()) == 0
    assert len(filter_manager.get_filtered_items()) == 0
    assert filter_manager.get_filter_status() == "Showing all 0 items"


def test_complex_filtering_scenario(sample_items):
    """Test a complex filtering scenario with mode changes."""
    filter_manager = FilterManager(sample_items)

    # Start with OR mode, add python and testing tags
    filter_manager.add_tag_filter("python")
    filter_manager.add_tag_filter("testing")

    # OR mode: should get 3 items (python OR testing)
    # Items: Python Library (both), Python Web Framework (python), Testing Tool (both)
    or_results = filter_manager.get_filtered_items()
    assert len(or_results) == 3

    # Switch to AND mode: should get 2 items (both python AND testing)
    # Items: Python Library, Testing Tool
    filter_manager.set_filter_mode(FilterMode.AND)
    and_results = filter_manager.get_filtered_items()
    assert len(and_results) == 2
    expected_titles = {"Python Library", "Testing Tool"}
    actual_titles = {item["title"] for item in and_results}
    assert actual_titles == expected_titles

    # Add framework tag: should get 1 item (Testing Tool has all three)
    filter_manager.add_tag_filter("framework")
    final_results = filter_manager.get_filtered_items()
    assert len(final_results) == 1
    assert final_results[0]["title"] == "Testing Tool"


# ==== Topic Filter Tests ====


def test_topic_counts_calculation(sample_items):
    """Test topic counts are calculated correctly."""
    filter_manager = FilterManager(sample_items)
    topic_counts = filter_manager.get_topic_counts()

    # Check expected topic counts
    assert topic_counts["Programming Languages"] == 2
    assert topic_counts["Web Development"] == 2
    assert topic_counts["Developer Tools"] == 1


def test_available_topics_sorted(sample_items):
    """Test available topics are returned sorted."""
    filter_manager = FilterManager(sample_items)
    topics = filter_manager.get_available_topics()

    assert topics == sorted(topics)
    assert "Developer Tools" in topics
    assert "Programming Languages" in topics
    assert "Web Development" in topics


def test_add_topic_filter(sample_items):
    """Test adding topic filters."""
    filter_manager = FilterManager(sample_items)

    # Add Programming Languages topic filter
    filter_manager.add_topic_filter("Programming Languages")

    assert "Programming Languages" in filter_manager.get_selected_topics()
    assert len(filter_manager.get_selected_topics()) == 1

    # Should return all items with this topic
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 2

    # Check titles of filtered items
    titles = {item["title"] for item in filtered_items}
    expected_titles = {"Python Library", "Testing Tool"}
    assert titles == expected_titles


def test_remove_topic_filter(sample_items):
    """Test removing topic filters."""
    filter_manager = FilterManager(sample_items)

    # Add and then remove a filter
    filter_manager.add_topic_filter("Web Development")
    assert "Web Development" in filter_manager.get_selected_topics()

    filter_manager.remove_topic_filter("Web Development")
    assert "Web Development" not in filter_manager.get_selected_topics()
    assert len(filter_manager.get_filtered_items()) == 5  # Back to all items


def test_toggle_topic_filter(sample_items):
    """Test toggling topic filters."""
    filter_manager = FilterManager(sample_items)

    # Toggle on
    filter_manager.toggle_topic_filter("Developer Tools")
    assert "Developer Tools" in filter_manager.get_selected_topics()

    # Toggle off
    filter_manager.toggle_topic_filter("Developer Tools")
    assert "Developer Tools" not in filter_manager.get_selected_topics()


def test_topic_and_tag_combined_filtering(sample_items):
    """Test combining topic and tag filters."""
    filter_manager = FilterManager(sample_items)

    # Add topic filter for "Web Development"
    filter_manager.add_topic_filter("Web Development")
    # Add tag filter for "python"
    filter_manager.add_tag_filter("python")

    # Should get intersection: items with Web Development topic AND python tag
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 1
    assert filtered_items[0]["title"] == "Python Web Framework"


def test_multiple_topics_or_logic(sample_items):
    """Test OR logic with multiple topics."""
    filter_manager = FilterManager(sample_items)

    # Add multiple topic filters
    filter_manager.add_topic_filter("Programming Languages")
    filter_manager.add_topic_filter("Developer Tools")

    # Should return items from either topic
    filtered_items = filter_manager.get_filtered_items()
    assert len(filtered_items) == 3  # 2 + 1

    titles = {item["title"] for item in filtered_items}
    expected_titles = {
        "Python Library",
        "Testing Tool",
        "Documentation Generator",
    }
    assert titles == expected_titles


def test_clear_filters_includes_topics(sample_items):
    """Test clearing all filters includes topics."""
    filter_manager = FilterManager(sample_items)

    # Add both tag and topic filters
    filter_manager.add_tag_filter("python")
    filter_manager.add_topic_filter("Web Development")
    assert len(filter_manager.get_selected_tags()) == 1
    assert len(filter_manager.get_selected_topics()) == 1

    # Clear all
    filter_manager.clear_filters()
    assert len(filter_manager.get_selected_tags()) == 0
    assert len(filter_manager.get_selected_topics()) == 0
    assert len(filter_manager.get_filtered_items()) == 5


def test_has_active_filters_includes_topics(sample_items):
    """Test has_active_filters includes topics."""
    filter_manager = FilterManager(sample_items)

    # No filters
    assert not filter_manager.has_active_filters()

    # Add topic filter
    filter_manager.add_topic_filter("Developer Tools")
    assert filter_manager.has_active_filters()

    # Clear topic filter
    filter_manager.remove_topic_filter("Developer Tools")
    assert not filter_manager.has_active_filters()

    # Add tag filter
    filter_manager.add_tag_filter("python")
    assert filter_manager.has_active_filters()


def test_filter_status_with_topics(sample_items):
    """Test filter status includes topic information."""
    filter_manager = FilterManager(sample_items)

    # No filters
    status = filter_manager.get_filter_status()
    assert status == "Showing all 5 items"

    # Single topic filter
    filter_manager.add_topic_filter("Web Development")
    status = filter_manager.get_filter_status()
    assert "2 of 5 items" in status
    assert "1 filter active" in status
    assert "topic" in status

    # Add tag filter
    filter_manager.add_tag_filter("python")
    status = filter_manager.get_filter_status()
    assert (
        "1 of 5 items" in status
    )  # Intersection of Web Development topic and python tag
    assert "2 filters active" in status
    assert "1 topic, 1 tag" in status


def test_update_items_includes_topics(sample_items):
    """Test updating items refreshes topic counts and filters."""
    filter_manager = FilterManager(sample_items)

    # Add topic filter
    filter_manager.add_topic_filter("Programming Languages")
    assert len(filter_manager.get_filtered_items()) == 2

    # Update with new items (subset)
    new_items = sample_items[:3]  # Only first 3 items
    filter_manager.update_items(new_items)

    # Should still have topic filter but fewer results
    assert "Programming Languages" in filter_manager.get_selected_topics()
    assert len(filter_manager.get_filtered_items()) == 1  # Only Python Library

    # Topic counts should be updated
    topic_counts = filter_manager.get_topic_counts()
    assert topic_counts["Programming Languages"] == 1
    assert topic_counts["Web Development"] == 2


def test_invalid_topic_handling(sample_items):
    """Test handling of invalid/non-existent topics."""
    filter_manager = FilterManager(sample_items)

    # Try to add non-existent topic
    filter_manager.add_topic_filter("Nonexistent Topic")

    # Should not be added to selected topics
    assert "Nonexistent Topic" not in filter_manager.get_selected_topics()
    assert len(filter_manager.get_selected_topics()) == 0

    # Try to remove non-existent topic (should not error)
    filter_manager.remove_topic_filter("Nonexistent Topic")
    assert len(filter_manager.get_selected_topics()) == 0


def test_items_without_topic_field():
    """Test handling items without topic field."""
    # Create item without topic field to test default handling
    items_without_topic: list[AwesomeListItem] = [
        {
            "title": "No Topic Item",
            "link": "https://example.com",
            "description": "An item without topic",
            "tags": ["test"],
            "sections": ["Test"],
            "topic": "",  # Empty topic to test default handling
        }
    ]

    filter_manager = FilterManager(items_without_topic)
    topic_counts = filter_manager.get_topic_counts()

    # Should default to "Unknown" for empty topics
    assert topic_counts["Unknown"] == 1
    assert len(filter_manager.get_available_topics()) == 1


def test_filter_summary_includes_topics(sample_items):
    """Test filter summary includes topic filter counts."""
    filter_manager = FilterManager(sample_items)

    # No filters
    total, filtered, active = filter_manager.get_filter_summary()
    assert total == 5
    assert filtered == 5
    assert active == 0

    # With topic and tag filters
    filter_manager.add_topic_filter("Programming Languages")
    filter_manager.add_tag_filter("python")

    total, filtered, active = filter_manager.get_filter_summary()
    assert total == 5
    assert (
        filtered == 2
    )  # Intersection of Programming Languages topic and python tag
    assert active == 2  # 1 topic + 1 tag
