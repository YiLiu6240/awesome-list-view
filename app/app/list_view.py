"""List view widget for displaying awesome list items.

This module provides the main list view component that displays awesome list
items in a scrollable, selectable list with keyboard navigation.
"""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import ListItem, ListView, Static

from app.funcs.editor_manager import EditorManager
from app.funcs.schema import AwesomeListItem
from app.funcs.url_manager import URLManager


class TagDisplay(Static):
    """Widget for displaying tags in a formatted way."""

    DEFAULT_CSS = """
    TagDisplay {
        color: $success;
        text-style: italic;
    }
    """

    def __init__(self, tags: list[str], max_display: int = 5):
        self.tags = tags
        self.max_display = max_display

        # Format tags for display
        display_tags = tags[:max_display]
        if len(tags) > max_display:
            tag_text = (
                " ".join(f"#{tag}" for tag in display_tags)
                + f" +{len(tags) - max_display}"
            )
        else:
            tag_text = " ".join(f"#{tag}" for tag in display_tags)

        super().__init__(tag_text)


class AwesomeListItemWidget(Static):
    """Widget representing a single awesome list item with search highlighting."""

    DEFAULT_CSS = """
    AwesomeListItemWidget {
        layout: vertical;
        height: auto;
        padding: 0 1;
    }

    AwesomeListItemWidget .title {
        text-style: bold;
        color: $text;
        width: 100%;
        text-wrap: nowrap;
        text-overflow: ellipsis;
        max-height: 2;
    }

    AwesomeListItemWidget .info {
        layout: horizontal;
        height: 1;
    }

    AwesomeListItemWidget .tags {
        color: $success;
        text-style: italic;
    }

    AwesomeListItemWidget .link-indicator {
        color: $secondary;
        width: 6;
    }

    AwesomeListItemWidget.--highlight {
        background: $background 30%;
    }

    AwesomeListItemWidget .search-highlight {
        background: $warning;
        color: $warning-darken-2;
        text-style: bold;
    }
    """

    def __init__(
        self,
        item: AwesomeListItem,
        index: int,
        search_matches: list[tuple[int, int]] | None = None,
    ):
        super().__init__()
        self.item = item
        self.index = index
        self.is_selected = False
        self.search_matches = search_matches or []

    def _highlight_text(self, text: str, matches: list[tuple[int, int]]) -> str:
        """Apply search highlighting to text using rich markup.

        Args:
            text: Original text
            matches: List of (start, end) positions to highlight

        Returns:
            Text with rich markup for highlighting
        """
        if not matches or not text:
            return text

        # Sort matches by start position
        sorted_matches = sorted(matches, key=lambda x: x[0])

        # Build highlighted text
        result = []
        last_end = 0

        for start, end in sorted_matches:
            # Ensure bounds are within text
            start = max(0, min(start, len(text)))
            end = max(start, min(end, len(text)))

            # Add text before match
            if start > last_end:
                result.append(text[last_end:start])

            # Add highlighted match
            if end > start:
                highlighted = text[start:end]
                result.append(
                    f"[reverse $accent]{highlighted}[/reverse $accent]"
                )

            last_end = end

        # Add remaining text
        if last_end < len(text):
            result.append(text[last_end:])

        return "".join(result)

    def compose(self) -> ComposeResult:
        """Compose the item widget with search highlighting."""
        # Title with highlighting
        title = self.item["title"]

        # Apply search highlighting to title
        if self.search_matches:
            title = self._highlight_text(title, self.search_matches)

        # Use full title - let Textual handle wrapping/truncation based on available space
        yield Static(title, classes="title")

        with Horizontal(classes="info"):
            # Link indicator
            link_indicator = "[link]" if self.item["link"] else "      "
            yield Static(link_indicator, classes="link-indicator")

            # Tags
            if self.item["tags"]:
                yield TagDisplay(self.item["tags"], max_display=6)
            else:
                yield Static("", classes="tags")

    def set_selected(self, selected: bool):
        """Set the selection state of this item."""
        self.is_selected = selected
        if selected:
            self.add_class("--highlight")
        else:
            self.remove_class("--highlight")

    def update_search_matches(self, matches: list[tuple[int, int]]):
        """Update search match positions and refresh display.

        Args:
            matches: List of (start, end) positions in the title
        """
        self.search_matches = matches
        # Trigger a re-compose to update highlighting
        self.remove_children()
        for widget in self.compose():
            self.mount(widget)


class AwesomeListView(Container):
    """Main list view for awesome list items with keyboard navigation."""

    # Allow this widget to receive focus
    can_focus = True

    class ItemSelected(Message):
        """Message sent when an item is selected."""

        def __init__(self, item: AwesomeListItem, index: int):
            super().__init__()
            self.item = item
            self.index = index

    class SelectionChanged(Message):
        """Message sent when selection changes."""

        def __init__(self, index: int, item: AwesomeListItem | None):
            super().__init__()
            self.index = index
            self.item = item

    DEFAULT_CSS = """
    AwesomeListView {
        border: solid $primary;
        height: 1fr;
        scrollbar-size: 1 1;
    }

    AwesomeListView ListView {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("up,k", "cursor_up", "Move up"),
        ("down,j", "cursor_down", "Move down"),
        ("home", "cursor_home", "Go to start"),
        ("end", "cursor_end", "Go to end"),
        ("enter", "select_item", "Select item"),
        ("o", "open_url", "Open URL"),
        ("e", "edit_item", "Edit item"),
    ]

    def __init__(self, items: list[AwesomeListItem] | None = None, app=None):
        super().__init__()
        self.items = items or []
        self.selected_index = -1
        self.list_view = ListView()
        self.search_matches: dict[
            int, list[tuple[int, int]]
        ] = {}  # item_index -> match positions
        self._selection_callbacks: list[
            Callable[[int, AwesomeListItem | None], None]
        ] = []
        self.url_manager = URLManager()
        self.editor_manager = EditorManager(app)

    def compose(self) -> ComposeResult:
        """Compose the list view."""
        yield self.list_view

    def focus(self, scroll_visible: bool = True):
        """Override focus to delegate to the inner ListView."""
        if self.list_view:
            return self.list_view.focus(scroll_visible)
        else:
            return super().focus(scroll_visible)

    def on_mount(self) -> None:
        """Initialize the list view when mounted."""
        self.refresh_items()
        # Ensure the inner ListView can receive focus
        if hasattr(self.list_view, "can_focus"):
            self.list_view.can_focus = True

    def set_items(self, items: list[AwesomeListItem]):
        """Update the items displayed in the list."""
        self.items = items
        self.selected_index = -1
        self.search_matches.clear()  # Clear search matches when items change
        self.refresh_items()

    def refresh_items(self):
        """Refresh the list view with current items."""
        self.list_view.clear()

        for i, item in enumerate(self.items):
            # Get search matches for this item index
            matches = self.search_matches.get(i, [])
            item_widget = AwesomeListItemWidget(item, i, matches)
            list_item = ListItem(item_widget)
            self.list_view.append(list_item)

        # Reset selection
        if self.items and self.selected_index < 0:
            self.select_item_by_index(0)

    def set_search_matches(self, matches: dict[int, list[tuple[int, int]]]):
        """Set search match positions for items.

        Args:
            matches: Dictionary mapping item index to list of (start, end) positions
        """
        self.search_matches = matches
        self._update_search_highlighting()

    def clear_search_matches(self):
        """Clear all search match highlighting."""
        self.search_matches.clear()
        self._update_search_highlighting()

    def _update_search_highlighting(self):
        """Update search highlighting for all visible items."""
        for i, list_item in enumerate(self.list_view.children):
            if hasattr(list_item, "children") and list_item.children:
                item_widget = list_item.children[0]
                if isinstance(item_widget, AwesomeListItemWidget):
                    matches = self.search_matches.get(i, [])
                    item_widget.update_search_matches(matches)

    def get_selected_item(self) -> AwesomeListItem | None:
        """Get the currently selected item."""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def select_item_by_index(self, index: int) -> bool:
        """Select an item by index."""
        if not (0 <= index < len(self.items)):
            return False

        # Update visual selection
        if 0 <= self.selected_index < len(self.list_view.children):
            # Remove highlight from previous selection
            prev_list_item = self.list_view.children[self.selected_index]
            if hasattr(prev_list_item, "children") and prev_list_item.children:
                prev_widget = prev_list_item.children[0]
                if isinstance(prev_widget, AwesomeListItemWidget):
                    prev_widget.set_selected(False)

        self.selected_index = index

        # Add highlight to new selection
        if 0 <= index < len(self.list_view.children):
            current_list_item = self.list_view.children[index]
            if (
                hasattr(current_list_item, "children")
                and current_list_item.children
            ):
                current_widget = current_list_item.children[0]
                if isinstance(current_widget, AwesomeListItemWidget):
                    current_widget.set_selected(True)

            # Update ListView selection
            self.list_view.index = index

        # Notify selection change
        selected_item = self.get_selected_item()
        self.post_message(self.SelectionChanged(index, selected_item))

        # Call callbacks
        for callback in self._selection_callbacks:
            callback(index, selected_item)

        return True

    def add_selection_callback(
        self, callback: Callable[[int, AwesomeListItem | None], None]
    ):
        """Add a callback to be called when selection changes."""
        self._selection_callbacks.append(callback)

    def action_cursor_up(self) -> None:
        """Move selection up one item."""
        new_index = max(0, self.selected_index - 1)
        self.select_item_by_index(new_index)

    def action_cursor_down(self) -> None:
        """Move selection down one item."""
        new_index = min(len(self.items) - 1, self.selected_index + 1)
        self.select_item_by_index(new_index)

    def action_page_up(self) -> None:
        """Move selection up by one page."""
        page_size = max(1, self.size.height - 2)  # Account for borders
        new_index = max(0, self.selected_index - page_size)
        self.select_item_by_index(new_index)

    def action_page_down(self) -> None:
        """Move selection down by one page."""
        page_size = max(1, self.size.height - 2)  # Account for borders
        new_index = min(len(self.items) - 1, self.selected_index + page_size)
        self.select_item_by_index(new_index)

    def action_cursor_home(self) -> None:
        """Move selection to first item."""
        if self.items:
            self.select_item_by_index(0)

    def action_cursor_end(self) -> None:
        """Move selection to last item."""
        if self.items:
            self.select_item_by_index(len(self.items) - 1)

    def action_select_item(self) -> None:
        """Select/activate the current item."""
        selected_item = self.get_selected_item()
        if selected_item:
            self.post_message(
                self.ItemSelected(selected_item, self.selected_index)
            )

    def action_open_url(self) -> None:
        """Open the URL of the currently selected item."""
        selected_item = self.get_selected_item()
        if not selected_item:
            return

        url = selected_item.get("link", "").strip()
        if not url:
            # Show error message via app notification system
            self.notify("No URL available for this item", severity="warning")
            return

        success = self.url_manager.open_url(url)
        if success:
            self.notify(f"Opened: {url}", severity="information")
        else:
            error = self.url_manager.get_last_error()
            self.notify(f"Failed to open URL: {error}", severity="error")

    def action_edit_item(self) -> None:
        """Edit the currently selected item in external text editor."""
        selected_item = self.get_selected_item()
        if not selected_item:
            self.notify("No item selected for editing", severity="warning")
            return

        # Create a copy to avoid modifying the original
        item_copy = dict(selected_item)  # type: ignore[assignment]

        self.notify("Opening item in editor...", severity="information")

        try:
            # Edit the item
            changes = self.editor_manager.edit_item(item_copy)  # type: ignore[arg-type]

            if changes is not None:
                # Source file was opened successfully or changes were made
                if changes:
                    # Apply changes to the original item (legacy temporary file editing)
                    for key, value in changes.items():
                        if key in selected_item:
                            selected_item[key] = value

                    self.notify(
                        "Item updated successfully", severity="information"
                    )

                    # Refresh the display
                    self.set_items(self.items)
                    self.select_item_by_index(self.selected_index)
                else:
                    # Empty dict means source file was opened successfully (no parsing back)
                    self.notify(
                        "Source file opened in editor", severity="information"
                    )
            else:
                # None means cancelled or failed - check for errors
                error = self.editor_manager.get_last_error()
                if error:
                    self.notify(
                        f"Failed to edit item: {error}", severity="error"
                    )
                else:
                    self.notify(
                        "Edit cancelled or no changes made",
                        severity="information",
                    )

        except Exception as e:
            error = self.editor_manager.get_last_error()
            self.notify(
                f"Failed to edit item: {error or str(e)}", severity="error"
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView selection events."""
        self.select_item_by_index(event.list_view.index or 0)

    def get_item_count(self) -> int:
        """Get the total number of items."""
        return len(self.items)
