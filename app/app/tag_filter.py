"""Tag filtering dialog for awesome list items.

This module provides a modal dialog for selecting tags to filter the
awesome list items with visual feedback and keyboard navigation.
"""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static

from app.funcs.filter_manager import FilterManager, FilterMode


class TagCheckbox(Horizontal):
    """A checkbox widget for tag selection with count display using text indicators."""

    DEFAULT_CSS = """
    TagCheckbox {
        height: 1;
        padding: 0 1;
    }

    TagCheckbox:hover {
        background: $secondary 20%;
    }

    TagCheckbox .tag-checkbox {
        width: 2;
        color: $text;
        text-align: left;
    }

    TagCheckbox .tag-name {
        width: 1fr;
        color: $text;
    }

    TagCheckbox .tag-count {
        width: 6;
        text-align: right;
        color: $accent;
        text-style: italic;
    }
    """

    def __init__(self, tag: str, count: int, checked: bool = False):
        super().__init__()
        self.tag = tag
        self.count = count
        self.is_checked = checked
        self.checkbox_label = Static(
            self._get_checkbox_text(), classes="tag-checkbox"
        )

    def _get_checkbox_text(self) -> str:
        """Get the text representation of the checkbox state."""
        return "●" if self.is_checked else "○"

    def compose(self) -> ComposeResult:
        yield self.checkbox_label
        yield Static(self.tag, classes="tag-name")
        yield Static(f"({self.count})", classes="tag-count")

    def toggle(self) -> None:
        """Toggle the checkbox state."""
        self.is_checked = not self.is_checked
        new_text = self._get_checkbox_text()
        # Try multiple update methods to ensure the text changes
        try:
            # Method 1: Standard update
            self.checkbox_label.update(new_text)

            # Method 2: Set renderable directly
            if hasattr(self.checkbox_label, "renderable"):
                self.checkbox_label.renderable = new_text

            # Method 3: Force refresh
            self.checkbox_label.refresh()

        except Exception:
            # Fallback: recreate the label if all else fails
            self.checkbox_label.remove()
            self.checkbox_label = Static(new_text, classes="tag-checkbox")
            self.mount(self.checkbox_label, before=0)

        # Post message to parent about tag toggle
        self.post_message(TagFilter.TagToggled(self.tag, self.is_checked))

    def set_checked(self, checked: bool) -> None:
        """Set the checkbox state."""
        if self.is_checked != checked:
            self.is_checked = checked
            new_text = self._get_checkbox_text()
            # Try multiple update methods to ensure the text changes
            try:
                # Method 1: Standard update
                self.checkbox_label.update(new_text)

                # Method 2: Set renderable directly
                if hasattr(self.checkbox_label, "renderable"):
                    self.checkbox_label.renderable = new_text

                # Method 3: Force refresh
                self.checkbox_label.refresh()

            except Exception:
                # Fallback: recreate the label if all else fails
                self.checkbox_label.remove()
                self.checkbox_label = Static(new_text, classes="tag-checkbox")
                self.mount(self.checkbox_label, before=0)

            # Post message to parent about tag toggle
            self.post_message(TagFilter.TagToggled(self.tag, self.is_checked))

    def on_click(self) -> None:
        """Handle click events to toggle the checkbox."""
        self.toggle()

    def on_list_item_selected(self) -> None:
        """Handle when this item is selected in the list."""
        # This allows clicking on the entire row to toggle
        self.toggle()


class TagFilter(ModalScreen[dict[str, bool] | None]):
    """Tag filter modal dialog widget."""

    class TagToggled(Message):
        """Message sent when a tag is toggled."""

        def __init__(self, tag: str, checked: bool):
            super().__init__()
            self.tag = tag
            self.checked = checked

    class FilterModeChanged(Message):
        """Message sent when filter mode changes."""

        def __init__(self, mode: FilterMode):
            super().__init__()
            self.mode = mode

    class ClearFilters(Message):
        """Message sent when clear filters is requested."""

        def __init__(self):
            super().__init__()

    CSS = """
    TagFilter {
        align: center middle;
    }

    TagFilter .dialog {
        width: 60;
        height: 30;
        max-width: 90%;
        max-height: 90%;
        border: round $primary;
        background: $panel;
        padding: 1;
    }

    TagFilter .header {
        dock: top;
        height: 1;
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    TagFilter .mode-section {
        dock: top;
        height: 3;
        margin-bottom: 1;
    }

    TagFilter .mode-toggle {
        width: 1fr;
    }

    TagFilter .tag-list {
        height: 1fr;
        scrollbar-size: 1 1;
        border: solid $secondary;
        margin-bottom: 1;
    }

    TagFilter .actions {
        dock: bottom;
        height: 3;
        layout: horizontal;
    }

    TagFilter .actions Button {
        width: 1fr;
        margin: 0 1;
    }

    TagFilter .status {
        text-align: center;
        color: $accent;
        text-style: italic;
        height: 1;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("space", "toggle_current_tag", "Toggle tag"),
        ("c", "clear_filters", "Clear filters"),
        ("m", "toggle_filter_mode", "Toggle filter mode"),
        ("up,k", "cursor_up", "Move up"),
        ("down,j", "cursor_down", "Move down"),
        ("escape", "cancel", "Cancel"),
        ("enter", "ok", "OK"),
    ]

    def __init__(self, filter_manager: FilterManager):
        super().__init__()
        self.filter_manager = filter_manager
        self.tag_checkboxes: dict[str, TagCheckbox] = {}
        self.sorted_tag_names: list[str] = []
        self.selected_tag_index = 0
        self.tag_list = ListView()
        self._initial_selected_tags = set(filter_manager.get_selected_tags())
        self._current_selections: dict[str, bool] = {}

    def compose(self) -> ComposeResult:
        """Compose the tag filter modal dialog."""
        with Vertical(classes="dialog"):
            # Header
            yield Label("Tag Filters", classes="header")

            # Filter mode section
            with Container(classes="mode-section"):
                mode_text = f"Mode: {self.filter_manager.get_filter_mode().value.upper()}"
                yield Button(mode_text, id="mode-toggle", classes="mode-toggle")

            # Tag list
            with Container(classes="tag-list"):
                yield self.tag_list

            # Status
            yield Label("", id="status-label", classes="status")

            # Actions
            with Horizontal(classes="actions"):
                yield Button("Clear All", id="clear-button")
                yield Button("OK", id="ok-button", variant="primary")
                yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        """Initialize the tag filter when mounted."""
        self.refresh_tags()
        self.update_status()
        self.tag_list.focus()

    def refresh_tags(self) -> None:
        """Refresh the tag list with current data."""
        self.tag_list.clear()
        self.tag_checkboxes.clear()
        self.sorted_tag_names.clear()
        self._current_selections.clear()

        tag_counts = self.filter_manager.get_tag_counts()
        selected_tags = self.filter_manager.get_selected_tags()

        # Sort tags alphabetically and maintain order
        sorted_tags = sorted(tag_counts.items())
        self.sorted_tag_names = [tag for tag, count in sorted_tags]

        for tag, count in sorted_tags:
            is_checked = tag in selected_tags
            self._current_selections[tag] = is_checked
            tag_checkbox = TagCheckbox(tag, count, is_checked)
            self.tag_checkboxes[tag] = tag_checkbox

            list_item = ListItem(tag_checkbox)
            self.tag_list.append(list_item)

        # Update selected index if needed
        if self.selected_tag_index >= len(sorted_tags):
            self.selected_tag_index = max(0, len(sorted_tags) - 1)

        # Update mode button
        self._update_mode_button()

    def _update_mode_button(self) -> None:
        """Update the filter mode button text."""
        try:
            mode_button = self.query_one("#mode-toggle", Button)
            mode_text = (
                f"Mode: {self.filter_manager.get_filter_mode().value.upper()}"
            )
            mode_button.label = mode_text
        except Exception:
            pass

    def update_status(self) -> None:
        """Update the status message."""
        try:
            status_label = self.query_one("#status-label", Label)
            selected_count = sum(
                1 for selected in self._current_selections.values() if selected
            )
            total_count = len(self.tag_checkboxes)

            if selected_count == 0:
                status_text = f"No tags selected ({total_count} available)"
            else:
                status_text = f"{selected_count} of {total_count} tags selected"

            status_label.update(status_text)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "mode-toggle":
            self.action_toggle_filter_mode()
        elif event.button.id == "clear-button":
            self.action_clear_filters()
        elif event.button.id == "ok-button":
            self.action_ok()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def on_tag_filter_tag_toggled(self, event: TagToggled) -> None:
        """Handle tag toggle events from checkboxes."""
        self._current_selections[event.tag] = event.checked
        self.update_status()

    def on_list_view_selected(self, event) -> None:
        """Handle list item selection/clicks."""
        # Toggle the selected tag when clicked
        self.action_toggle_current_tag()

    def action_toggle_current_tag(self) -> None:
        """Toggle the currently highlighted tag."""
        if not self.tag_checkboxes or not self.sorted_tag_names:
            return

        # Get current tag from ListView selection using sorted order
        if self.tag_list.index is not None:
            if 0 <= self.tag_list.index < len(self.sorted_tag_names):
                tag = self.sorted_tag_names[self.tag_list.index]
                tag_checkbox = self.tag_checkboxes[tag]
                tag_checkbox.toggle()

    def action_clear_filters(self) -> None:
        """Clear all tag filters."""
        # Update all checkboxes
        for tag_checkbox in self.tag_checkboxes.values():
            tag_checkbox.set_checked(False)

        # Update current selections
        self._current_selections = dict.fromkeys(
            self._current_selections, False
        )
        self.update_status()

    def action_toggle_filter_mode(self) -> None:
        """Toggle between AND/OR filter mode."""
        self.filter_manager.toggle_filter_mode()
        self._update_mode_button()

    def action_cursor_up(self) -> None:
        """Move cursor up in tag list."""
        if self.tag_list.index is not None and self.tag_list.index > 0:
            self.tag_list.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down in tag list."""
        if self.tag_list.index is not None:
            max_index = len(self.sorted_tag_names) - 1
            if self.tag_list.index < max_index:
                self.tag_list.index += 1

    def action_ok(self) -> None:
        """Apply changes and close the dialog."""
        # Apply current selections to filter manager
        for tag, selected in self._current_selections.items():
            if selected:
                self.filter_manager.add_tag_filter(tag)
            else:
                self.filter_manager.remove_tag_filter(tag)

        # Return the current selections
        self.dismiss(self._current_selections)

    def action_cancel(self) -> None:
        """Cancel changes and close the dialog."""
        # Restore original selections
        for tag in self._current_selections:
            original_selected = tag in self._initial_selected_tags
            self.filter_manager.remove_tag_filter(tag)
            if original_selected:
                self.filter_manager.add_tag_filter(tag)

        # Return None to indicate cancellation
        self.dismiss(None)

    def on_key(self, event) -> None:  # type: ignore[override]
        """Handle key events."""
        if getattr(event, "key", "") == "escape":
            self.action_cancel()

    def get_filter_status(self) -> str:
        """Get current filter status for display."""
        return self.filter_manager.get_filter_status()

    def get_selected_tags_count(self) -> int:
        """Get the number of currently selected tags."""
        return sum(
            1 for selected in self._current_selections.values() if selected
        )

    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return any(self._current_selections.values())

    def add_tag_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Add a callback for tag toggle events - legacy compatibility."""
        pass

    def update_filter_manager(self, filter_manager: FilterManager) -> None:
        """Update the filter manager and refresh display - legacy compatibility."""
        self.filter_manager = filter_manager
        self.refresh_tags()

    # Legacy compatibility methods for existing tests
    def action_close_filter(self) -> None:
        """Close the filter panel - legacy compatibility."""
        self.action_cancel()
