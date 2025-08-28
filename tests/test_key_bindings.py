"""Tests for key bindings and search functionality."""

from unittest.mock import MagicMock, patch

from app.cli import AwesomeListApp
from app.funcs.schema import AwesomeListItem


class TestKeyBindings:
    """Test key bindings and their corresponding actions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = AwesomeListApp()

        # Mock some basic items
        self.sample_items: list[AwesomeListItem] = [
            {
                "title": "Python Framework",
                "description": "Django web framework",
                "tags": ["python", "web"],
                "link": "https://djangoproject.com",
                "sections": ["Web"],
                "topic": "Python",
            },
            {
                "title": "JavaScript Library",
                "description": "React UI library",
                "tags": ["javascript", "ui"],
                "link": "https://reactjs.org",
                "sections": ["Frontend"],
                "topic": "JavaScript",
            },
        ]

        self.app.items = self.sample_items.copy()
        self.app.all_items = self.sample_items.copy()

    def test_search_key_binding_exists(self):
        """Test that the search key binding is properly configured."""
        # Check that the slash key binding exists in BINDINGS
        binding_keys = [binding[0] for binding in self.app.BINDINGS]
        binding_actions = [binding[1] for binding in self.app.BINDINGS]

        assert "slash" in binding_keys
        slash_index = binding_keys.index("slash")
        assert binding_actions[slash_index] == "focus_search"

    def test_topic_filter_key_binding_exists(self):
        """Test that the topic filter key binding is properly configured."""
        # Check that the 't' key binding exists in BINDINGS
        binding_keys = [binding[0] for binding in self.app.BINDINGS]
        binding_actions = [binding[1] for binding in self.app.BINDINGS]

        assert "t" in binding_keys
        t_index = binding_keys.index("t")
        assert binding_actions[t_index] == "open_topic_filter"

    def test_tag_filter_key_bindings_exist(self):
        """Test that the tag filter key bindings are properly configured."""
        # Check that the 'f' and 'space' key bindings exist in BINDINGS
        binding_keys = [binding[0] for binding in self.app.BINDINGS]
        binding_actions = [binding[1] for binding in self.app.BINDINGS]

        assert "f" in binding_keys
        f_index = binding_keys.index("f")
        assert binding_actions[f_index] == "open_tag_filter"

        assert "space" in binding_keys
        space_index = binding_keys.index("space")
        assert binding_actions[space_index] == "open_tag_filter"

    @patch("app.cli.SearchModal")
    def test_action_focus_search_creates_modal(self, mock_modal_class):
        """Test that action_focus_search creates and shows a SearchModal."""
        mock_modal = MagicMock()
        mock_modal_class.return_value = mock_modal

        self.app.push_screen = MagicMock()
        self.app.current_query = "test query"

        # Call the action
        self.app.action_focus_search()

        # Verify modal was created with current query
        mock_modal_class.assert_called_once_with("test query")

        # Verify push_screen was called with modal and callback
        self.app.push_screen.assert_called_once()
        args, kwargs = self.app.push_screen.call_args
        assert args[0] is mock_modal
        assert callable(args[1])  # callback function

    @patch("app.cli.SearchModal")
    def test_search_result_handler_apply(self, mock_modal_class):
        """Test search result handler applies search correctly."""
        mock_modal = MagicMock()
        mock_modal_class.return_value = mock_modal

        self.app.push_screen = MagicMock()
        self.app.apply_search = MagicMock()
        self.app.clear_search = MagicMock()

        # Call action to get the callback
        self.app.action_focus_search()
        args, kwargs = self.app.push_screen.call_args
        callback = args[1]

        # Test with non-empty result
        callback("python web")
        self.app.apply_search.assert_called_once_with("python web")
        self.app.clear_search.assert_not_called()

    @patch("app.cli.SearchModal")
    def test_search_result_handler_clear(self, mock_modal_class):
        """Test search result handler clears search for empty input."""
        mock_modal = MagicMock()
        mock_modal_class.return_value = mock_modal

        self.app.push_screen = MagicMock()
        self.app.apply_search = MagicMock()
        self.app.clear_search = MagicMock()

        # Call action to get the callback
        self.app.action_focus_search()
        args, kwargs = self.app.push_screen.call_args
        callback = args[1]

        # Test with empty result (whitespace only)
        callback("   ")
        self.app.clear_search.assert_called_once()
        self.app.apply_search.assert_not_called()

    @patch("app.cli.SearchModal")
    def test_search_result_handler_cancel(self, mock_modal_class):
        """Test search result handler does nothing on cancel/escape."""
        mock_modal = MagicMock()
        mock_modal_class.return_value = mock_modal

        self.app.push_screen = MagicMock()
        self.app.apply_search = MagicMock()
        self.app.clear_search = MagicMock()

        # Call action to get the callback
        self.app.action_focus_search()
        args, kwargs = self.app.push_screen.call_args
        callback = args[1]

        # Test with None result (cancel/escape)
        callback(None)
        self.app.clear_search.assert_not_called()
        self.app.apply_search.assert_not_called()

    def test_initial_query_handling(self):
        """Test that initial query is handled correctly."""
        # Test with no current_query attribute
        if hasattr(self.app, "current_query"):
            delattr(self.app, "current_query")

        with patch("app.cli.SearchModal") as mock_modal_class:
            mock_modal = MagicMock()
            mock_modal_class.return_value = mock_modal
            self.app.push_screen = MagicMock()

            self.app.action_focus_search()

            # Should be called with empty string when no current_query
            mock_modal_class.assert_called_once_with("")

        # Test with current_query set
        self.app.current_query = "existing search"

        with patch("app.cli.SearchModal") as mock_modal_class:
            mock_modal = MagicMock()
            mock_modal_class.return_value = mock_modal
            self.app.push_screen = MagicMock()

            self.app.action_focus_search()

            # Should be called with existing query
            mock_modal_class.assert_called_once_with("existing search")


class TestSearchIntegration:
    """Test search functionality integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = AwesomeListApp()

        # Mock items for testing
        self.sample_items: list[AwesomeListItem] = [
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
                "title": "PostgreSQL",
                "description": "Advanced database system",
                "tags": ["database", "sql"],
                "link": "https://postgresql.org",
                "sections": ["Databases"],
                "topic": "Database",
            },
        ]

        self.app.items = self.sample_items.copy()
        self.app.all_items = self.sample_items.copy()

    def test_search_functionality_with_real_data(self):
        """Test search functionality with actual item filtering."""
        # Test title search
        self.app.apply_search("Django")
        assert len(self.app.items) == 1
        assert self.app.items[0]["title"] == "Django"
        assert self.app.current_query == "Django"

        # Test description search
        self.app.apply_search("UI library")
        assert len(self.app.items) == 1
        assert self.app.items[0]["title"] == "React"

        # Test tag search
        self.app.apply_search("database")
        assert len(self.app.items) == 1
        assert self.app.items[0]["title"] == "PostgreSQL"

        # Test case insensitive
        self.app.apply_search("PYTHON")
        assert len(self.app.items) == 1
        assert self.app.items[0]["title"] == "Django"

        # Test no matches
        self.app.apply_search("nonexistent")
        assert len(self.app.items) == 0
        assert self.app.current_query == "nonexistent"

        # Test clearing search
        self.app.clear_search()
        assert len(self.app.items) == 3
        assert self.app.current_query == ""

    def test_search_error_handling(self):
        """Test search error handling with edge cases."""
        # Test with empty all_items list
        self.app.all_items = []
        self.app.apply_search("test")
        # Should result in empty items
        assert len(self.app.items) == 0

        # Reset items
        self.app.all_items = self.sample_items.copy()

        # Test with empty search string
        self.app.apply_search("")
        assert len(self.app.items) == 3
        assert self.app.current_query == ""

        # Test with whitespace only
        self.app.apply_search("   ")
        assert len(self.app.items) == 3
        assert self.app.current_query == ""

        # Test with special characters
        self.app.apply_search("@#$%")
        assert len(self.app.items) == 0
        assert self.app.current_query == "@#$%"

    def test_search_with_filter_manager_integration(self):
        """Test search integration with filter manager."""
        # Mock filter manager
        from app.funcs.filter_manager import FilterManager

        self.app.filter_manager = FilterManager(self.app.items)

        # Test search with filter manager
        self.app.apply_search("python")

        # Verify filter manager was updated
        assert self.app.filter_manager.get_search_query() == "python"
        assert self.app.filter_manager.has_search_results()

        # Test clearing search with filter manager
        self.app.clear_search()
        assert self.app.filter_manager.get_search_query() == ""
        assert not self.app.filter_manager.has_search_results()
