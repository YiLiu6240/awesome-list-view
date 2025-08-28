"""Tests for the EditorManager functionality.

This module tests the source file editing behavior to ensure
the "e" key opens source files instead of temporary files.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.funcs.editor_manager import EditorManager
from app.funcs.schema import AwesomeListItem


class TestEditorManager:
    """Test cases for EditorManager source file editing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.editor_manager = EditorManager()
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

    def create_test_item(
        self, source_file: str, line_number: int = 10
    ) -> AwesomeListItem:
        """Create a test AwesomeListItem with source file information."""
        return {
            "title": "Test Item",
            "link": "https://example.com",
            "description": "A test item",
            "tags": ["test", "example"],
            "sections": ["Section 1"],
            "topic": "Test Topic",
            "source_file": source_file,
            "line_number": line_number,
        }

    def test_edit_item_opens_source_file(self):
        """Test that edit_item opens the source file directly."""
        # Create test source file
        content = """# Test Awesome List

## Section 1

- [Test Item](https://example.com) - A test item #test #example
"""
        source_file = self.create_test_source_file(content)
        item = self.create_test_item(source_file, 5)

        # Mock the editor command execution
        with patch.object(
            self.editor_manager, "open_file_in_editor_with_line"
        ) as mock_open:
            mock_open.return_value = True

            # Call edit_item
            result = self.editor_manager.edit_item(item)

            # Verify source file was opened with correct line number
            mock_open.assert_called_once_with(source_file, 5)
            assert result == {}

    def test_edit_item_with_missing_source_file(self):
        """Test edit_item behavior when source file is missing."""
        # Create item with non-existent source file
        item = self.create_test_item("/non/existent/file.md", 10)

        # Call edit_item
        result = self.editor_manager.edit_item(item)

        # Should return None and set error
        assert result is None
        error = self.editor_manager.get_last_error()
        assert error is not None and "Source file not found" in error

    def test_edit_item_with_no_source_file_info(self):
        """Test edit_item behavior when item has no source file information."""
        # Create item without source file info
        item = self.create_test_item("unknown", 0)

        # Call edit_item
        result = self.editor_manager.edit_item(item)

        # Should return None and set error
        assert result is None
        error = self.editor_manager.get_last_error()
        assert (
            error is not None
            and "No source file information available" in error
        )

    def test_open_file_in_editor_with_line_vscode(self):
        """Test opening file with line number in VS Code."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["code"]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock()

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 10
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["code", "-g", f"{source_file}:10"], check=True
                )

    def test_open_file_in_editor_with_line_vim(self):
        """Test opening file with line number in Vim."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["vim"]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock()

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 10
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["vim", "+10", source_file], check=True
                )

    def test_open_file_in_editor_with_line_nano(self):
        """Test opening file with line number in Nano."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["nano"]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock()

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 10
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["nano", "+10", source_file], check=True
                )

    def test_open_file_in_editor_with_line_fallback(self):
        """Test opening file with unknown editor (fallback behavior)."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["unknown-editor"]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock()

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 10
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["unknown-editor", source_file], check=True
                )

    def test_open_file_in_editor_with_line_zero(self):
        """Test opening file with line number 0 (no line jump)."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["code"]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock()

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 0
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["code", source_file], check=True
                )

    def test_open_file_in_editor_with_line_editor_failure(self):
        """Test handling of editor command failure."""
        source_file = self.create_test_source_file("# Test content")

        with patch.object(
            self.editor_manager, "get_editor_command"
        ) as mock_get_cmd:
            mock_get_cmd.return_value = ["code"]

            with patch("subprocess.run") as mock_run:
                from subprocess import CalledProcessError

                mock_run.side_effect = CalledProcessError(1, "code")

                result = self.editor_manager.open_file_in_editor_with_line(
                    source_file, 10
                )

                assert result is False
                error = self.editor_manager.get_last_error()
                assert error is not None and "Editor command failed" in error

    @patch.dict(os.environ, {"EDITOR": "vim"})
    def test_environment_editor_preference(self):
        """Test that editor preference is read from environment."""
        editor_cmd = self.editor_manager.get_editor_command()
        assert editor_cmd == ["vim"]

    @patch.dict(os.environ, {"VISUAL": "code"})
    def test_visual_editor_preference(self):
        """Test that VISUAL takes precedence over EDITOR."""
        with patch.dict(os.environ, {"EDITOR": "vim"}):
            editor_cmd = self.editor_manager.get_editor_command()
            assert editor_cmd == ["code"]
