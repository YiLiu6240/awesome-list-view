"""Tests for TopicFilter modal functionality."""

from typing import Any
from unittest.mock import MagicMock

import pytest

try:
    from app.app.topic_filter import TopicCheckbox, TopicFilter
except ImportError:
    # Handle import error for test discovery
    TopicCheckbox = None  # type: ignore
    TopicFilter = None  # type: ignore

from app.funcs.filter_manager import FilterManager
from app.funcs.schema import AwesomeListItem


@pytest.fixture
def sample_items_with_topics() -> list[AwesomeListItem]:
    """Create sample items with topics for testing."""
    return [
        {
            "title": "Python Library",
            "link": "https://python.org",
            "description": "A Python library for testing",
            "tags": ["python", "library"],
            "sections": ["Development"],
            "topic": "Programming Languages",
        },
        {
            "title": "Web Framework",
            "link": "https://django.com",
            "description": "A web framework",
            "tags": ["web", "framework"],
            "sections": ["Web"],
            "topic": "Web Development",
        },
        {
            "title": "Testing Tool",
            "link": "https://pytest.org",
            "description": "A testing framework",
            "tags": ["testing"],
            "sections": ["Testing"],
            "topic": "Developer Tools",
        },
    ]


class TestTopicCheckbox:
    """Test TopicCheckbox widget functionality."""

    def test_topic_checkbox_initialization(self):
        """Test TopicCheckbox initialization."""
        if TopicCheckbox is None:
            pytest.skip("TopicCheckbox not available")

        checkbox = TopicCheckbox("Programming Languages", 5, checked=True)

        assert checkbox.topic == "Programming Languages"
        assert checkbox.count == 5
        assert checkbox.is_checked is True

    def test_topic_checkbox_toggle(self):
        """Test TopicCheckbox toggle functionality."""
        if TopicCheckbox is None:
            pytest.skip("TopicCheckbox not available")

        checkbox = TopicCheckbox("Web Development", 3, checked=False)

        # Initial state
        assert checkbox.is_checked is False

        # Toggle on
        checkbox.toggle()
        assert checkbox.is_checked is True

        # Toggle off
        checkbox.toggle()
        assert checkbox.is_checked is False

    def test_topic_checkbox_set_checked(self):
        """Test TopicCheckbox set_checked method."""
        if TopicCheckbox is None:
            pytest.skip("TopicCheckbox not available")

        checkbox = TopicCheckbox("Developer Tools", 2, checked=False)

        # Set to checked
        checkbox.set_checked(True)
        assert checkbox.is_checked is True

        # Set to unchecked
        checkbox.set_checked(False)
        assert checkbox.is_checked is False

        # Set same state (should not change)
        checkbox.set_checked(False)
        assert checkbox.is_checked is False


class TestTopicFilter:
    """Test TopicFilter modal functionality."""

    def test_topic_filter_initialization(self, sample_items_with_topics):
        """Test TopicFilter initialization."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        assert topic_filter.filter_manager is filter_manager
        assert isinstance(topic_filter.topic_checkboxes, dict)
        assert isinstance(topic_filter.sorted_topic_names, list)

    def test_refresh_topics(self, sample_items_with_topics):
        """Test topic list refresh functionality."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Mock the topic_list to avoid mounting issues
        topic_filter.topic_list = MagicMock()
        topic_filter.topic_list.clear = MagicMock()
        topic_filter.topic_list.append = MagicMock()

        # Mock the mode button update to avoid query issues
        topic_filter._update_mode_button: Any = MagicMock()

        topic_filter.refresh_topics()

        # Should have topics from our sample items
        expected_topics = [
            "Developer Tools",
            "Programming Languages",
            "Web Development",
        ]
        assert topic_filter.sorted_topic_names == expected_topics
        assert len(topic_filter.topic_checkboxes) == 3

    def test_action_toggle_current_topic(self, sample_items_with_topics):
        """Test toggling current topic action."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Set up mock topic checkboxes
        topic_filter.sorted_topic_names = [
            "Programming Languages",
            "Web Development",
        ]

        mock_checkbox = MagicMock()
        topic_filter.topic_checkboxes = {"Programming Languages": mock_checkbox}

        # Mock topic_list
        topic_filter.topic_list = MagicMock()
        topic_filter.topic_list.index = 0  # First item selected

        # Action should toggle the checkbox
        topic_filter.action_toggle_current_topic()
        mock_checkbox.toggle.assert_called_once()

    def test_action_clear_filters(self, sample_items_with_topics):
        """Test clearing all topic filters."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Set up mock checkboxes
        mock_checkbox1 = MagicMock()
        mock_checkbox2 = MagicMock()
        topic_filter.topic_checkboxes = {
            "Programming Languages": mock_checkbox1,
            "Web Development": mock_checkbox2,
        }
        topic_filter._current_selections = {
            "Programming Languages": True,
            "Web Development": False,
        }

        # Mock update_status to avoid query issues
        mock_update_status = MagicMock()
        topic_filter.update_status: Any = mock_update_status

        topic_filter.action_clear_filters()

        # All checkboxes should be set to unchecked
        mock_checkbox1.set_checked.assert_called_with(False)
        mock_checkbox2.set_checked.assert_called_with(False)

        # All selections should be False
        assert all(
            not selected
            for selected in topic_filter._current_selections.values()
        )

    def test_action_ok_applies_selections(self, sample_items_with_topics):
        """Test OK action applies current selections."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Set up current selections
        topic_filter._current_selections = {
            "Programming Languages": True,
            "Web Development": False,
            "Developer Tools": True,
        }

        # Mock dismiss method
        mock_dismiss = MagicMock()
        topic_filter.dismiss: Any = mock_dismiss

        topic_filter.action_ok()

        # Filter manager should have the selected topics
        selected_topics = filter_manager.get_selected_topics()
        assert "Programming Languages" in selected_topics
        assert "Developer Tools" in selected_topics
        assert "Web Development" not in selected_topics

        # Should dismiss with current selections
        mock_dismiss.assert_called_with(topic_filter._current_selections)

    def test_action_cancel_restores_original(self, sample_items_with_topics):
        """Test Cancel action restores original selections."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)

        # Add initial topic filter
        filter_manager.add_topic_filter("Programming Languages")

        topic_filter = TopicFilter(filter_manager)

        # Simulate changing selections
        topic_filter._current_selections = {
            "Programming Languages": False,  # Changed from True
            "Web Development": True,  # Added
        }

        # Mock dismiss method
        mock_dismiss = MagicMock()
        topic_filter.dismiss: Any = mock_dismiss

        topic_filter.action_cancel()

        # Should restore original state
        selected_topics = filter_manager.get_selected_topics()
        assert "Programming Languages" in selected_topics
        assert "Web Development" not in selected_topics

        # Should dismiss with None
        mock_dismiss.assert_called_with(None)

    def test_topic_toggle_message_handling(self, sample_items_with_topics):
        """Test handling of topic toggle messages."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Initialize selections
        topic_filter._current_selections = {"Programming Languages": False}

        # Mock update_status
        mock_update_status = MagicMock()
        topic_filter.update_status: Any = mock_update_status

        # Create and handle toggle message
        message = TopicFilter.TopicToggled("Programming Languages", True)
        topic_filter.on_topic_filter_topic_toggled(message)

        # Should update selections and status
        assert topic_filter._current_selections["Programming Languages"] is True
        mock_update_status.assert_called_once()

    def test_get_selected_topics_count(self, sample_items_with_topics):
        """Test getting selected topics count."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # Set up selections
        topic_filter._current_selections = {
            "Programming Languages": True,
            "Web Development": False,
            "Developer Tools": True,
        }

        count = topic_filter.get_selected_topics_count()
        assert count == 2

    def test_has_active_filters(self, sample_items_with_topics):
        """Test checking for active topic filters."""
        if TopicFilter is None:
            pytest.skip("TopicFilter not available")

        filter_manager = FilterManager(sample_items_with_topics)
        topic_filter = TopicFilter(filter_manager)

        # No selections
        topic_filter._current_selections = {
            "Programming Languages": False,
            "Web Development": False,
        }
        assert not topic_filter.has_active_filters()

        # With selections
        topic_filter._current_selections["Programming Languages"] = True
        assert topic_filter.has_active_filters()
