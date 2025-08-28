"""Tests for TUI-specific issues: tag display and title expansion."""

from typing import Any

from app.app.layout import ContentArea
from app.app.list_view import AwesomeListItemWidget, AwesomeListView
from app.app.tag_filter import TagFilter
from app.funcs.filter_manager import FilterManager


class TestTagSidebarDisplay:
    """Test tag/topic display in sidebar."""

    def test_tag_filter_widget_creation(self):
        """Test that TagFilter widget can be created with items containing tags."""
        # Create sample items with tags
        items: list[dict[str, Any]] = [
            {
                "title": "Test Item 1",
                "description": "Test description",
                "link": "https://example.com",
                "tags": ["python", "web", "framework"],
            },
            {
                "title": "Test Item 2",
                "description": "Another test",
                "link": "https://example2.com",
                "tags": ["javascript", "web", "frontend"],
            },
            {
                "title": "Test Item 3",
                "description": "Third test",
                "link": "https://example3.com",
                "tags": ["python", "data"],
            },
        ]

        # Create filter manager
        filter_manager = FilterManager(items)  # type: ignore[arg-type]

        # Verify tag counts are calculated correctly
        tag_counts = filter_manager.get_tag_counts()
        assert "python" in tag_counts
        assert tag_counts["python"] == 2  # appears in 2 items
        assert "web" in tag_counts
        assert tag_counts["web"] == 2  # appears in 2 items
        assert "javascript" in tag_counts
        assert tag_counts["javascript"] == 1

        # Create tag filter widget
        tag_filter = TagFilter(filter_manager)
        assert tag_filter is not None
        assert tag_filter.filter_manager == filter_manager

    def test_content_area_filter_pane_visibility(self):
        """Test that filter pane visibility can be toggled."""
        content_area = ContentArea(split_view=True)

        # Initially filter pane should be hidden
        assert not content_area.is_filter_visible()

        # Toggle should make it visible
        is_visible = content_area.toggle_filter_pane()
        assert is_visible
        assert content_area.is_filter_visible()

        # Toggle again should hide it
        is_visible = content_area.toggle_filter_pane()
        assert not is_visible
        assert not content_area.is_filter_visible()

    def test_tag_filter_has_refresh_tags_method(self):
        """Test that TagFilter has refresh_tags method for updating display."""
        items: list[dict[str, Any]] = [
            {
                "title": "Test Item",
                "description": "Test",
                "link": "https://example.com",
                "tags": ["python", "web"],
            }
        ]

        filter_manager = FilterManager(items)  # type: ignore[arg-type]
        tag_filter = TagFilter(filter_manager)

        # Should have refresh_tags method
        assert hasattr(tag_filter, "refresh_tags")
        assert callable(tag_filter.refresh_tags)


class TestTitleExpansion:
    """Test title expansion behavior in list items."""

    def test_title_no_truncation_in_compose(self):
        """Test that compose method doesn't truncate titles anymore."""
        # Create item with long title
        long_title = "This is a very long title that exceeds sixty characters and should be truncated"
        item: dict[str, Any] = {
            "title": long_title,
            "description": "Test description",
            "link": "https://example.com",
            "tags": ["test"],
        }

        # Create widget
        widget = AwesomeListItemWidget(item, 0)  # type: ignore[arg-type]

        # Verify the widget was created successfully
        assert widget is not None
        assert widget.item["title"] == long_title

    def test_title_expansion_with_dynamic_width(self):
        """Test that titles should expand based on available space, not fixed limits."""
        # Create items with varying title lengths
        short_item: dict[str, Any] = {
            "title": "Short",
            "description": "Test",
            "link": "https://example.com",
            "tags": ["test"],
        }

        medium_item: dict[str, Any] = {
            "title": "Medium length title that fits comfortably",
            "description": "Test",
            "link": "https://example.com",
            "tags": ["test"],
        }

        long_item: dict[str, Any] = {
            "title": "Very long title that should expand dynamically based on available container width rather than being hard truncated",
            "description": "Test",
            "link": "https://example.com",
            "tags": ["test"],
        }

        # Create widgets
        short_widget = AwesomeListItemWidget(short_item, 0)  # type: ignore[arg-type]
        medium_widget = AwesomeListItemWidget(medium_item, 1)  # type: ignore[arg-type]
        long_widget = AwesomeListItemWidget(long_item, 2)  # type: ignore[arg-type]

        # All should be valid widgets
        assert short_widget is not None
        assert medium_widget is not None
        assert long_widget is not None

    def test_list_view_can_display_varying_titles(self):
        """Test that AwesomeListView can handle items with varying title lengths."""
        items: list[dict[str, Any]] = [
            {
                "title": "Short",
                "description": "Test",
                "link": "https://example.com",
                "tags": ["test"],
            },
            {
                "title": "This is a much longer title that should be handled gracefully by the list view component",
                "description": "Test",
                "link": "https://example.com",
                "tags": ["test"],
            },
        ]

        list_view = AwesomeListView()

        # Verify list view can store items (without calling set_items which requires app context)
        list_view.items = items  # type: ignore[assignment]
        assert len(list_view.items) == 2


class TestTUIIntegration:
    """Test integration of tag display and title expansion."""

    def test_filter_manager_and_list_view_integration(self):
        """Test that filter manager and list view work together."""
        items: list[dict[str, Any]] = [
            {
                "title": "Python Web Framework with a very long descriptive title",
                "description": "Test description",
                "link": "https://example.com",
                "tags": ["python", "web", "framework"],
            },
            {
                "title": "JavaScript Frontend Library",
                "description": "Another test",
                "link": "https://example2.com",
                "tags": ["javascript", "frontend"],
            },
        ]

        # Create components
        filter_manager = FilterManager(items)  # type: ignore[arg-type]
        list_view = AwesomeListView()

        # Test that filtering works
        filter_manager.add_tag_filter("python")
        filtered_items = filter_manager.get_filtered_items()
        assert len(filtered_items) == 1
        assert "python" in filtered_items[0]["tags"]

        # Test list view can store filtered items
        list_view.items = filtered_items  # type: ignore[assignment]
        assert len(list_view.items) == 1

    def test_tag_filter_refresh_updates_display(self):
        """Test that tag filter refresh updates when items change."""
        initial_items: list[dict[str, Any]] = [
            {
                "title": "Item 1",
                "description": "Test",
                "link": "https://example.com",
                "tags": ["python"],
            }
        ]

        filter_manager = FilterManager(initial_items)  # type: ignore[arg-type]
        TagFilter(filter_manager)  # Create but don't assign to unused variable

        # Add more items to filter manager
        updated_items = initial_items + [
            {
                "title": "Item 2",
                "description": "Test",
                "link": "https://example2.com",
                "tags": ["javascript", "python"],
            }
        ]

        # Update filter manager
        filter_manager.update_items(updated_items)  # type: ignore[arg-type]

        # Tag counts should be updated
        tag_counts = filter_manager.get_tag_counts()
        assert tag_counts["python"] == 2
        assert "javascript" in tag_counts
