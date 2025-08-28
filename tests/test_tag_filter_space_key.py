"""Tests for Space key toggle functionality in TagFilter widget."""

from unittest.mock import MagicMock

import pytest

from app.app.tag_filter import TagCheckbox, TagFilter
from app.funcs.filter_manager import FilterManager


@pytest.fixture
def sample_items():
    """Sample items with tags for testing."""
    return [
        {
            "title": "Django",
            "description": "Python web framework",
            "tags": ["python", "web", "framework"],
            "link": "https://djangoproject.com",
            "sections": ["Web Frameworks"],
            "topic": "Python",
        },
        {
            "title": "React",
            "description": "JavaScript UI library",
            "tags": ["javascript", "ui", "library"],
            "link": "https://reactjs.org",
            "sections": ["Frontend"],
            "topic": "JavaScript",
        },
        {
            "title": "Flask",
            "description": "Lightweight Python web framework",
            "tags": ["python", "web", "micro"],
            "link": "https://flask.palletsprojects.com",
            "sections": ["Web Frameworks"],
            "topic": "Python",
        },
    ]


@pytest.fixture
def filter_manager(sample_items):
    """Filter manager instance for testing."""
    return FilterManager(sample_items)


@pytest.fixture
def tag_filter(filter_manager):
    """TagFilter widget instance for testing."""
    return TagFilter(filter_manager)


class TestTagFilterSpaceKey:
    """Test Space key functionality in TagFilter widget."""

    def test_tag_filter_has_space_binding(self, tag_filter):
        """Test that TagFilter has space key binding configured."""
        # Check that space binding exists
        binding_keys = [binding[0] for binding in tag_filter.BINDINGS]
        binding_actions = [binding[1] for binding in tag_filter.BINDINGS]

        assert "space" in binding_keys
        space_index = binding_keys.index("space")
        assert binding_actions[space_index] == "toggle_current_tag"

    def test_action_toggle_current_tag_method_exists(self, tag_filter):
        """Test that action_toggle_current_tag method exists and is callable."""
        assert hasattr(tag_filter, "action_toggle_current_tag")
        assert callable(tag_filter.action_toggle_current_tag)

    def test_tag_checkbox_toggle_method(self):
        """Test TagCheckbox toggle method works correctly."""
        tag_checkbox = TagCheckbox("python", 2, checked=False)

        # Initial state
        assert not tag_checkbox.is_checked

        # Toggle once
        tag_checkbox.toggle()
        assert tag_checkbox.is_checked

        # Toggle again
        tag_checkbox.toggle()
        assert not tag_checkbox.is_checked

    def test_tag_checkbox_set_checked_method(self):
        """Test TagCheckbox set_checked method works correctly."""
        tag_checkbox = TagCheckbox("python", 2, checked=False)

        # Set to checked
        tag_checkbox.set_checked(True)
        assert tag_checkbox.is_checked

        # Set to unchecked
        tag_checkbox.set_checked(False)
        assert not tag_checkbox.is_checked

    def test_action_toggle_current_tag_with_no_tags(self, tag_filter):
        """Test action_toggle_current_tag when no tags are available."""
        # Clear any existing tags
        tag_filter.tag_checkboxes.clear()

        # Should not raise an error
        tag_filter.action_toggle_current_tag()

    def test_action_toggle_current_tag_with_no_selection(self, tag_filter):
        """Test action_toggle_current_tag when no tag is selected."""
        # Mock the tag list to have tags but no selection
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = None
        tag_filter.tag_checkboxes = {"python": TagCheckbox("python", 2)}

        # Should not raise an error
        tag_filter.action_toggle_current_tag()

    def test_action_toggle_current_tag_with_invalid_index(self, tag_filter):
        """Test action_toggle_current_tag with invalid index."""
        # Mock the tag list with invalid index
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 999  # Invalid index
        tag_filter.tag_checkboxes = {"python": TagCheckbox("python", 2)}

        # Should not raise an error
        tag_filter.action_toggle_current_tag()

    def test_action_toggle_current_tag_valid_selection(self, tag_filter):
        """Test action_toggle_current_tag with valid tag selection."""
        # Setup mock tag list and checkboxes
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 0

        # Setup sorted tag names and checkboxes
        tag_filter.sorted_tag_names = ["python", "web"]

        # Create mock tag checkboxes
        python_checkbox = MagicMock(spec=TagCheckbox)
        web_checkbox = MagicMock(spec=TagCheckbox)

        tag_filter.tag_checkboxes = {
            "python": python_checkbox,
            "web": web_checkbox,
        }

        # Call action_toggle_current_tag
        tag_filter.action_toggle_current_tag()

        # Verify the first tag was toggled
        python_checkbox.toggle.assert_called_once()
        web_checkbox.toggle.assert_not_called()

    def test_action_toggle_current_tag_second_selection(self, tag_filter):
        """Test action_toggle_current_tag with second tag selected."""
        # Setup mock tag list and checkboxes
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 1  # Select second tag

        # Setup sorted tag names and checkboxes
        tag_filter.sorted_tag_names = ["python", "web"]

        # Create mock tag checkboxes
        python_checkbox = MagicMock(spec=TagCheckbox)
        web_checkbox = MagicMock(spec=TagCheckbox)

        tag_filter.tag_checkboxes = {
            "python": python_checkbox,
            "web": web_checkbox,
        }

        # Call action_toggle_current_tag
        tag_filter.action_toggle_current_tag()

        # Verify the second tag was toggled
        python_checkbox.toggle.assert_not_called()
        web_checkbox.toggle.assert_called_once()

    def test_tag_filter_integration_with_filter_manager(self, filter_manager):
        """Test TagFilter integration with FilterManager for space key."""
        tag_filter = TagFilter(filter_manager)

        # Mock the tag list and avoid calling refresh_tags (which requires mounting)
        tag_filter.tag_list = MagicMock()

        # Manually setup sorted_tag_names and tag_checkboxes to simulate refresh_tags
        tag_counts = filter_manager.get_tag_counts()
        sorted_tags = sorted(tag_counts.items())
        tag_filter.sorted_tag_names = [tag for tag, count in sorted_tags]

        for tag, count in sorted_tags:
            tag_checkbox = TagCheckbox(tag, count, checked=False)
            tag_filter.tag_checkboxes[tag] = tag_checkbox

        # Verify tags were loaded
        assert len(tag_filter.tag_checkboxes) > 0

        # Select first tag and toggle it
        tag_filter.tag_list.index = 0

        # Toggle the tag
        tag_filter.action_toggle_current_tag()

        # Check if the checkbox state changed
        first_tag = tag_filter.sorted_tag_names[0]
        checkbox = tag_filter.tag_checkboxes[first_tag]
        assert checkbox.is_checked  # Should now be checked

    def test_tag_checkbox_message_posting(self):
        """Test that TagCheckbox posts messages when checked state changes."""
        tag_checkbox = TagCheckbox("python", 2, checked=False)

        # Mock the post_message method
        mock_post_message = MagicMock()
        tag_checkbox.post_message = mock_post_message  # type: ignore[method-assign]

        # Test toggle functionality posts messages
        tag_checkbox.toggle()
        mock_post_message.assert_called()
        assert tag_checkbox.is_checked

        # Reset mock and test set_checked functionality
        mock_post_message.reset_mock()
        tag_checkbox.set_checked(False)
        mock_post_message.assert_called()
        assert not tag_checkbox.is_checked


class TestTagFilterKeyboardNavigation:
    """Test keyboard navigation in TagFilter widget."""

    def test_cursor_navigation_bindings(self, tag_filter):
        """Test that cursor navigation bindings are properly configured."""
        binding_keys = [binding[0] for binding in tag_filter.BINDINGS]
        binding_actions = [binding[1] for binding in tag_filter.BINDINGS]

        # Check up/k binding
        assert "up,k" in binding_keys
        up_index = binding_keys.index("up,k")
        assert binding_actions[up_index] == "cursor_up"

        # Check down/j binding
        assert "down,j" in binding_keys
        down_index = binding_keys.index("down,j")
        assert binding_actions[down_index] == "cursor_down"

    def test_action_cursor_up(self, tag_filter):
        """Test cursor up navigation."""
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 2

        tag_filter.action_cursor_up()

        # Should decrement index
        assert tag_filter.tag_list.index == 1

    def test_action_cursor_up_at_top(self, tag_filter):
        """Test cursor up navigation at top of list."""
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 0

        tag_filter.action_cursor_up()

        # Should stay at 0 (not go negative)
        assert tag_filter.tag_list.index == 0

    def test_action_cursor_down(self, tag_filter):
        """Test cursor down navigation."""
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 1
        tag_filter.sorted_tag_names = ["tag1", "tag2", "tag3"]

        tag_filter.action_cursor_down()

        # Should increment index
        assert tag_filter.tag_list.index == 2

    def test_action_cursor_down_at_bottom(self, tag_filter):
        """Test cursor down navigation at bottom of list."""
        tag_filter.tag_list = MagicMock()
        tag_filter.sorted_tag_names = ["tag1", "tag2"]
        tag_filter.tag_list.index = 1  # Last item (0-indexed)

        tag_filter.action_cursor_down()

        # Should stay at last index
        assert tag_filter.tag_list.index == 1


class TestTagFilterRealWorldScenarios:
    """Test real-world scenarios for space key functionality."""

    def test_space_key_workflow_scenario(self, filter_manager):
        """Test complete workflow: navigate and toggle tags with space key."""
        tag_filter = TagFilter(filter_manager)

        # Initialize with real data without calling refresh_tags
        tag_filter.tag_list = MagicMock()

        # Manually setup sorted_tag_names and tag_checkboxes to simulate refresh_tags
        tag_counts = filter_manager.get_tag_counts()
        sorted_tags = sorted(tag_counts.items())
        tag_filter.sorted_tag_names = [tag for tag, count in sorted_tags]

        for tag, count in sorted_tags:
            tag_checkbox = TagCheckbox(tag, count, checked=False)
            tag_filter.tag_checkboxes[tag] = tag_checkbox

        # Should have tags from sample data
        assert len(tag_filter.tag_checkboxes) > 0

        # Start at first tag
        tag_filter.tag_list.index = 0

        # Toggle first tag with space
        first_tag = (
            tag_filter.sorted_tag_names[0]
            if tag_filter.sorted_tag_names
            else None
        )
        if first_tag:
            initial_state = tag_filter.tag_checkboxes[first_tag].is_checked
            tag_filter.action_toggle_current_tag()
            new_state = tag_filter.tag_checkboxes[first_tag].is_checked
            assert new_state != initial_state

        # Move down and toggle another tag
        if len(tag_filter.sorted_tag_names) > 1:
            tag_filter.action_cursor_down()
            assert tag_filter.tag_list.index == 1

            second_tag = tag_filter.sorted_tag_names[1]
            initial_state = tag_filter.tag_checkboxes[second_tag].is_checked
            tag_filter.action_toggle_current_tag()
            new_state = tag_filter.tag_checkboxes[second_tag].is_checked
            assert new_state != initial_state

    def test_empty_filter_manager_space_key(self):
        """Test space key behavior with empty filter manager."""
        empty_filter_manager = FilterManager([])
        tag_filter = TagFilter(empty_filter_manager)

        # Mock tag list
        tag_filter.tag_list = MagicMock()
        tag_filter.tag_list.index = 0

        # Should not crash with empty tags
        tag_filter.action_toggle_current_tag()

        # Verify no tags exist
        assert len(tag_filter.tag_checkboxes) == 0
