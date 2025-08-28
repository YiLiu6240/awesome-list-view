"""Editor integration functionality for editing items via text editor.

This module provides cross-platform text editor integration
with proper error handling and file watching capabilities.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from .schema import AwesomeListItem

if TYPE_CHECKING:
    from textual.app import App


class EditorManager:
    """Manages opening and editing items in external text editor."""

    def __init__(self, app: "App | None" = None):
        """Initialize the editor manager.

        Args:
            app: Optional Textual app instance for suspend/resume functionality
        """
        self._last_error: str | None = None
        self._temp_files: list[str] = []
        self._app = app

    def get_editor_command(self) -> list[str]:
        """Get the preferred text editor command.

        Returns:
            List of command parts for the editor
        """
        # Check environment variables for editor preference
        editor = (
            os.environ.get("VISUAL")
            or os.environ.get("EDITOR")
            or self._get_default_editor()
        )

        if not editor:
            self._last_error = "No editor found in environment"
            return []

        # Handle multi-word editor commands
        return editor.split()

    def _get_default_editor(self) -> str:
        """Get default editor based on platform.

        Returns:
            Default editor command
        """
        if sys.platform == "win32":
            # Windows: try notepad, then code, then notepad++
            for editor in ["code", "notepad++", "notepad"]:
                if self._is_command_available(editor):
                    return editor
        elif sys.platform == "darwin":
            # macOS: try VS Code, then TextEdit
            for editor in ["code", "open -t"]:
                if editor == "open -t" or self._is_command_available(editor):
                    return editor
        else:
            # Linux: try common editors
            for editor in ["code", "gedit", "nano", "vim"]:
                if self._is_command_available(editor):
                    return editor

        return ""

    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH.

        Args:
            command: Command to check

        Returns:
            True if command is available
        """
        try:
            subprocess.run(
                ["which", command]
                if sys.platform != "win32"
                else ["where", command],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_temp_file_for_item(self, item: AwesomeListItem) -> str | None:
        """Create a temporary file with item content for editing.

        Args:
            item: The item to create a temp file for

        Returns:
            Path to temporary file or None if failed
        """
        try:
            # Create content for editing
            content = self._format_item_for_editing(item)

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            self._temp_files.append(temp_path)
            return temp_path

        except Exception as e:
            self._last_error = f"Failed to create temporary file: {e}"
            return None

    def _format_item_for_editing(self, item: AwesomeListItem) -> str:
        """Format an item for editing in text editor.

        Args:
            item: The item to format

        Returns:
            Formatted content for editing
        """
        lines = [
            "# Edit Awesome List Item",
            "",
            "## Title",
            item["title"],
            "",
            "## Link",
            item["link"],
            "",
            "## Description",
            item["description"] or "(No description)",
            "",
            "## Tags",
            ", ".join(item["tags"]) if item["tags"] else "(No tags)",
            "",
            "## Sections",
            " → ".join(item["sections"])
            if item["sections"]
            else "(No sections)",
            "",
            "---",
            "",
            "Edit the content above. Only Title, Link, Description, and Tags will be saved.",
            "Changes to Sections will be ignored as they come from markdown structure.",
        ]

        return "\n".join(lines)

    def parse_edited_content(self, content: str) -> dict | None:
        """Parse edited content back into item fields.

        Args:
            content: The edited content

        Returns:
            Dictionary with updated fields or None if parsing failed
        """
        try:
            lines = content.split("\n")
            result = {}

            current_section = None
            content_lines = []

            for line in lines:
                line = line.strip()

                if line.startswith("## "):
                    # Save previous section
                    if current_section and content_lines:
                        section_content = "\n".join(content_lines).strip()
                        if current_section == "Title":
                            result["title"] = section_content
                        elif current_section == "Link":
                            result["link"] = section_content
                        elif current_section == "Description":
                            result["description"] = (
                                section_content
                                if section_content != "(No description)"
                                else ""
                            )
                        elif current_section == "Tags":
                            if section_content != "(No tags)":
                                # Parse comma-separated tags
                                tags = [
                                    tag.strip()
                                    for tag in section_content.split(",")
                                    if tag.strip()
                                ]
                                result["tags"] = tags
                            else:
                                result["tags"] = []

                    # Start new section
                    current_section = line[3:]  # Remove "## "
                    content_lines = []
                elif line.startswith("---"):
                    # End of editable content
                    break
                elif current_section:
                    content_lines.append(line)

            # Handle last section
            if current_section and content_lines:
                section_content = "\n".join(content_lines).strip()
                if current_section == "Title":
                    result["title"] = section_content
                elif current_section == "Link":
                    result["link"] = section_content
                elif current_section == "Description":
                    result["description"] = (
                        section_content
                        if section_content != "(No description)"
                        else ""
                    )
                elif current_section == "Tags":
                    if section_content != "(No tags)":
                        tags = [
                            tag.strip()
                            for tag in section_content.split(",")
                            if tag.strip()
                        ]
                        result["tags"] = tags
                    else:
                        result["tags"] = []

            return result

        except Exception as e:
            self._last_error = f"Failed to parse edited content: {e}"
            return None

    def open_file_in_editor_with_line(
        self, file_path: str, line_number: int = 0
    ) -> bool:
        """Open a file in the configured text editor at a specific line.

        Args:
            file_path: Path to file to edit
            line_number: Line number to jump to (0-based)

        Returns:
            True if editor was launched successfully
        """
        editor_cmd = self.get_editor_command()
        if not editor_cmd:
            return False

        try:
            # Build command with line number support for common editors
            cmd = editor_cmd[:]
            editor_name = editor_cmd[0].lower()

            # Add line number argument for supported editors
            if line_number > 0:
                if "code" in editor_name:  # VS Code
                    cmd.extend(["-g", f"{file_path}:{line_number}"])
                elif (
                    "vim" in editor_name or "nvim" in editor_name
                ):  # Vim/Neovim
                    cmd.extend([f"+{line_number}", file_path])
                elif "nano" in editor_name:  # Nano
                    cmd.extend([f"+{line_number}", file_path])
                elif "emacs" in editor_name:  # Emacs
                    cmd.extend([f"+{line_number}", file_path])
                elif "gedit" in editor_name:  # Gedit
                    cmd.extend([f"+{line_number}", file_path])
                else:
                    # Fallback: just open the file
                    cmd.append(file_path)
            else:
                cmd.append(file_path)

            # Suspend TUI app if available to allow editor to take control of terminal
            if self._app is not None:
                with self._app.suspend():
                    # Launch editor while TUI is suspended
                    subprocess.run(cmd, check=True)
            else:
                # Fallback for when no app is provided (testing scenarios)
                subprocess.run(cmd, check=True)

            self._last_error = None
            return True

        except subprocess.CalledProcessError as e:
            self._last_error = f"Editor command failed: {e}"
            return False
        except FileNotFoundError:
            self._last_error = f"Editor not found: {editor_cmd[0]}"
            return False
        except Exception as e:
            self._last_error = f"Failed to launch editor: {e}"
            return False

    def open_file_in_editor(self, file_path: str) -> bool:
        """Open a file in the configured text editor.

        Args:
            file_path: Path to file to edit

        Returns:
            True if editor was launched successfully
        """
        editor_cmd = self.get_editor_command()
        if not editor_cmd:
            return False

        try:
            # Suspend TUI app if available to allow editor to take control of terminal
            if self._app is not None:
                with self._app.suspend():
                    # Launch editor while TUI is suspended
                    subprocess.run(editor_cmd + [file_path], check=True)
            else:
                # Fallback for when no app is provided (testing scenarios)
                subprocess.run(editor_cmd + [file_path], check=True)

            self._last_error = None
            return True

        except subprocess.CalledProcessError as e:
            self._last_error = f"Editor command failed: {e}"
            return False
        except FileNotFoundError:
            self._last_error = f"Editor not found: {editor_cmd[0]}"
            return False
        except Exception as e:
            self._last_error = f"Failed to launch editor: {e}"
            return False

    def read_temp_file(self, file_path: str) -> str | None:
        """Read content from temporary file.

        Args:
            file_path: Path to temporary file

        Returns:
            File content or None if failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self._last_error = f"Failed to read temporary file: {e}"
            return None

    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files."""
        for file_path in self._temp_files[:]:
            try:
                if Path(file_path).exists():
                    os.unlink(file_path)
                self._temp_files.remove(file_path)
            except Exception:
                # Ignore cleanup errors
                pass

    def get_last_error(self) -> str | None:
        """Get the last error message.

        Returns:
            Last error message or None if no error
        """
        return self._last_error

    def edit_item(self, item: AwesomeListItem) -> dict | None:
        """Edit an item by opening the source file in the external text editor.

        Args:
            item: The item to edit

        Returns:
            Dictionary with updated fields or None if cancelled/failed
        """
        # Get source file path from item
        source_file = item.get("source_file", "")
        line_number = item.get("line_number", 0)

        if not source_file or source_file == "unknown":
            self._last_error = (
                "No source file information available for this item"
            )
            return None

        # Check if source file exists
        from pathlib import Path

        if not Path(source_file).exists():
            self._last_error = f"Source file not found: {source_file}"
            return None

        try:
            # Open source file in editor with line number support
            if not self.open_file_in_editor_with_line(source_file, line_number):
                return None

            # For now, we don't parse changes back since we're editing the source directly
            # The user will need to regenerate the cache to see changes
            return {}

        except Exception as e:
            self._last_error = f"Failed to open source file: {e}"
            return None

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup_temp_files()
