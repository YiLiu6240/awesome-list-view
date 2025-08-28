"""Integration tests for source file editing functionality.

This module tests the integration between the list view and editor manager
to ensure the "e" key binding correctly opens source files.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.app.list_view import AwesomeListView
from app.funcs.schema import AwesomeListItem


class TestSourceFileEditingIntegration:
    """Integration tests for source file editing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_test_source_file(self, content: str) -> str:
        """Create a test source file with given content."""
        source_file = Path(self.temp_dir) / "test_awesome_list.md"
        source_file.write_text(content, encoding="utf-8")
        return str(source_file)

    def create_test_items(self, source_file: str) -> list[AwesomeListItem]:
        """Create test items with source file information."""
        return [
            {
                "title": "First Item",
                "link": "https://example.com/1",
                "description": "First test item",
                "tags": ["test", "first"],
                "sections": ["Section 1"],
                "topic": "Test Topic",
                "source_file": source_file,
                "line_number": 5,
            },
            {
                "title": "Second Item",
                "link": "https://example.com/2",
                "description": "Second test item",
                "tags": ["test", "second"],
                "sections": ["Section 1"],
                "topic": "Test Topic",
                "source_file": source_file,
                "line_number": 6,
            },
        ]

    def test_list_view_edit_action_opens_source_file(self):
        """Test that the list view edit action opens the source file."""
        # Create test source file
        content = """# Test Awesome List

## Section 1

- [First Item](https://example.com/1) - First test item #test #first
- [Second Item](https://example.com/2) - Second test item #test #second
"""
        source_file = self.create_test_source_file(content)
        items = self.create_test_items(source_file)

        # Create list view with test items
        list_view = AwesomeListView(items)

        # Manually set up the list view to have the first item selected
        list_view.selected_index = 0  # Select first item

        # Mock the editor manager's edit_item method
        with patch.object(list_view.editor_manager, "edit_item") as mock_edit:
            mock_edit.return_value = {}

            # Mock the notify method to avoid GUI dependencies
            with patch.object(list_view, "notify") as mock_notify:
                # Trigger edit action
                list_view.action_edit_item()

                # Verify edit_item was called with the selected item
                mock_edit.assert_called_once()
                called_item = mock_edit.call_args[0][0]
                assert called_item["title"] == "First Item"
                assert called_item["source_file"] == source_file
                assert called_item["line_number"] == 5

                # Verify success notification
                mock_notify.assert_called_with(
                    "Source file opened in editor", severity="information"
                )

    def test_list_view_edit_action_handles_missing_source_file(self):
        """Test that the list view edit action handles missing source files gracefully."""
        # Create test items with non-existent source file
        items = self.create_test_items("/non/existent/file.md")

        # Create list view with test items
        list_view = AwesomeListView(items)

        # Manually set up the list view to have the first item selected
        list_view.selected_index = 0  # Select first item

        # Mock the editor manager's edit_item method to return None (failure)
        with patch.object(list_view.editor_manager, "edit_item") as mock_edit:
            mock_edit.return_value = None

            # Mock get_last_error to return a specific error
            with patch.object(
                list_view.editor_manager, "get_last_error"
            ) as mock_error:
                mock_error.return_value = (
                    "Source file not found: /non/existent/file.md"
                )

                # Mock the notify method to avoid GUI dependencies
                with patch.object(list_view, "notify") as mock_notify:
                    # Trigger edit action
                    list_view.action_edit_item()

                    # Verify edit_item was called
                    mock_edit.assert_called_once()

                    # Verify error notification - should be the second call
                    mock_notify.assert_any_call(
                        "Failed to edit item: Source file not found: /non/existent/file.md",
                        severity="error",
                    )

    def test_list_view_edit_action_no_item_selected(self):
        """Test that the list view edit action handles no selected item."""
        # Create empty list view
        list_view = AwesomeListView([])

        # Mock the notify method to avoid GUI dependencies
        with patch.object(list_view, "notify") as mock_notify:
            # Trigger edit action
            list_view.action_edit_item()

            # Verify warning notification
            mock_notify.assert_called_once_with(
                "No item selected for editing", severity="warning"
            )

    def test_editor_manager_integration_with_real_file(self):
        """Test EditorManager integration with a real file."""
        # Create test source file
        content = """# Test Awesome List

## Section 1

- [Test Item](https://example.com) - A test item #test #example
"""
        source_file = self.create_test_source_file(content)

        # Create test item
        item: AwesomeListItem = {
            "title": "Test Item",
            "link": "https://example.com",
            "description": "A test item",
            "tags": ["test", "example"],
            "sections": ["Section 1"],
            "topic": "Test Topic",
            "source_file": source_file,
            "line_number": 5,
        }

        # Create list view with test item
        list_view = AwesomeListView([item])

        # Manually set up the list view to have the first item selected
        list_view.selected_index = 0  # Select first item

        # Mock the subprocess.run to avoid actually opening an editor
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock()

            # Mock get_editor_command to return a known editor
            with patch.object(
                list_view.editor_manager, "get_editor_command"
            ) as mock_get_cmd:
                mock_get_cmd.return_value = ["code"]

                # Mock the notify method to avoid GUI dependencies
                with patch.object(list_view, "notify") as mock_notify:
                    # Trigger edit action
                    list_view.action_edit_item()

                    # Verify subprocess.run was called with correct arguments
                    mock_run.assert_called_once_with(
                        ["code", "-g", f"{source_file}:5"], check=True
                    )

                    # Verify success notification
                    mock_notify.assert_called_with(
                        "Source file opened in editor", severity="information"
                    )
