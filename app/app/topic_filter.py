"""Topic filtering dialog for awesome list items.

This module provides a modal dialog for selecting topics to filter the
awesome list items with visual feedback and keyboard navigation.
"""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Static

from app.funcs.filter_manager import FilterManager, FilterMode


class TopicCheckbox(Horizontal):
    """A checkbox widget for topic selection with count display using text indicators."""

    DEFAULT_CSS = """
    TopicCheckbox {
        height: 1;
        padding: 0 1;
    }

    TopicCheckbox:hover {
        background: $secondary 20%;
    }

    TopicCheckbox .topic-checkbox {
        width: 2;
        color: $text;
        text-align: left;
    }

    TopicCheckbox .topic-name {
        width: 1fr;
        color: $text;
    }

    TopicCheckbox .topic-count {
        width: 6;
        text-align: right;
        color: $accent;
        text-style: italic;
    }
    """

    def __init__(self, topic: str, count: int, checked: bool = False):
        super().__init__()
        self.topic = topic
        self.count = count
        self.is_checked = checked
        self.checkbox_label = Static(
            self._get_checkbox_text(), classes="topic-checkbox"
        )

    def _get_checkbox_text(self) -> str:
        """Get the text representation of the checkbox state."""
        return "●" if self.is_checked else "○"

    def compose(self) -> ComposeResult:
        yield self.checkbox_label
        yield Static(self.topic, classes="topic-name")
        yield Static(f"({self.count})", classes="topic-count")

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
            self.checkbox_label = Static(new_text, classes="topic-checkbox")
            self.mount(self.checkbox_label, before=0)

        # Post message to parent about topic toggle
        self.post_message(TopicFilter.TopicToggled(self.topic, self.is_checked))

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
                self.checkbox_label = Static(new_text, classes="topic-checkbox")
                self.mount(self.checkbox_label, before=0)

            # Post message to parent about topic toggle
            self.post_message(
                TopicFilter.TopicToggled(self.topic, self.is_checked)
            )

    def on_click(self) -> None:
        """Handle click events to toggle the checkbox."""
        self.toggle()

    def on_list_item_selected(self) -> None:
        """Handle when this item is selected in the list."""
        # This allows clicking on the entire row to toggle
        self.toggle()


class TopicFilter(ModalScreen[dict[str, bool] | None]):
    """Topic filter modal dialog widget."""

    class TopicToggled(Message):
        """Message sent when a topic is toggled."""

        def __init__(self, topic: str, checked: bool):
            super().__init__()
            self.topic = topic
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
    TopicFilter {
        align: center middle;
    }

    TopicFilter .dialog {
        width: 60;
        height: 30;
        max-width: 90%;
        max-height: 90%;
        border: round $primary;
        background: $panel;
        padding: 1;
    }

    TopicFilter .header {
        dock: top;
        height: 1;
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    TopicFilter .mode-section {
        dock: top;
        height: 3;
        margin-bottom: 1;
    }

    TopicFilter .mode-toggle {
        width: 1fr;
    }

    TopicFilter .topic-list {
        height: 1fr;
        scrollbar-size: 1 1;
        border: solid $secondary;
        margin-bottom: 1;
    }

    TopicFilter .actions {
        dock: bottom;
        height: 3;
        layout: horizontal;
    }

    TopicFilter .actions Button {
        width: 1fr;
        margin: 0 1;
    }

    TopicFilter .status {
        text-align: center;
        color: $accent;
        text-style: italic;
        height: 1;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("space", "toggle_current_topic", "Toggle topic"),
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
        self.topic_checkboxes: dict[str, TopicCheckbox] = {}
        self.sorted_topic_names: list[str] = []
        self.selected_topic_index = 0
        self.topic_list = ListView()
        self._initial_selected_topics = set(
            filter_manager.get_selected_topics()
        )
        self._current_selections: dict[str, bool] = {}

    def compose(self) -> ComposeResult:
        """Compose the topic filter modal dialog."""
        with Vertical(classes="dialog"):
            # Header
            yield Label("Topic Filters", classes="header")

            # Filter mode section (for consistency with tag filter)
            with Container(classes="mode-section"):
                mode_text = "Mode: OR (topics are mutually exclusive)"
                yield Button(mode_text, id="mode-toggle", classes="mode-toggle")

            # Topic list
            with Container(classes="topic-list"):
                yield self.topic_list

            # Status
            yield Label("", id="status-label", classes="status")

            # Actions
            with Horizontal(classes="actions"):
                yield Button("Clear All", id="clear-button")
                yield Button("OK", id="ok-button", variant="primary")
                yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        """Initialize the topic filter when mounted."""
        self.refresh_topics()
        self.update_status()
        self.topic_list.focus()

    def refresh_topics(self) -> None:
        """Refresh the topic list with current data."""
        self.topic_list.clear()
        self.topic_checkboxes.clear()
        self.sorted_topic_names.clear()
        self._current_selections.clear()

        topic_counts = self.filter_manager.get_topic_counts()
        selected_topics = self.filter_manager.get_selected_topics()

        # Sort topics alphabetically and maintain order
        sorted_topics = sorted(topic_counts.items())
        self.sorted_topic_names = [topic for topic, count in sorted_topics]

        for topic, count in sorted_topics:
            is_checked = topic in selected_topics
            self._current_selections[topic] = is_checked
            topic_checkbox = TopicCheckbox(topic, count, is_checked)
            self.topic_checkboxes[topic] = topic_checkbox

            list_item = ListItem(topic_checkbox)
            self.topic_list.append(list_item)

        # Update selected index if needed
        if self.selected_topic_index >= len(sorted_topics):
            self.selected_topic_index = max(0, len(sorted_topics) - 1)

        # Update mode button
        self._update_mode_button()

    def _update_mode_button(self) -> None:
        """Update the filter mode button text."""
        try:
            mode_button = self.query_one("#mode-toggle", Button)
            # For topics, OR semantics make most sense since items have one topic
            mode_text = "Mode: OR (topics are mutually exclusive)"
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
            total_count = len(self.topic_checkboxes)

            if selected_count == 0:
                status_text = f"No topics selected ({total_count} available)"
            else:
                status_text = (
                    f"{selected_count} of {total_count} topics selected"
                )

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

    def on_topic_filter_topic_toggled(self, event: TopicToggled) -> None:
        """Handle topic toggle events from checkboxes."""
        self._current_selections[event.topic] = event.checked
        self.update_status()

    def on_list_view_selected(self, event) -> None:
        """Handle list item selection/clicks."""
        # Toggle the selected topic when clicked
        self.action_toggle_current_topic()

    def action_toggle_current_topic(self) -> None:
        """Toggle the currently highlighted topic."""
        if not self.topic_checkboxes or not self.sorted_topic_names:
            return

        # Get current topic from ListView selection using sorted order
        if self.topic_list.index is not None:
            if 0 <= self.topic_list.index < len(self.sorted_topic_names):
                topic = self.sorted_topic_names[self.topic_list.index]
                topic_checkbox = self.topic_checkboxes[topic]
                topic_checkbox.toggle()

    def action_clear_filters(self) -> None:
        """Clear all topic filters."""
        # Update all checkboxes
        for topic_checkbox in self.topic_checkboxes.values():
            topic_checkbox.set_checked(False)

        # Update current selections
        self._current_selections = dict.fromkeys(
            self._current_selections, False
        )
        self.update_status()

    def action_toggle_filter_mode(self) -> None:
        """Toggle filter mode (no-op for topics since OR is most logical)."""
        # Topics are naturally OR since items have one topic
        # Keep this for UI consistency but make it a no-op
        pass

    def action_cursor_up(self) -> None:
        """Move cursor up in topic list."""
        if self.topic_list.index is not None and self.topic_list.index > 0:
            self.topic_list.index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down in topic list."""
        if self.topic_list.index is not None:
            max_index = len(self.sorted_topic_names) - 1
            if self.topic_list.index < max_index:
                self.topic_list.index += 1

    def action_ok(self) -> None:
        """Apply changes and close the dialog."""
        # Apply current selections to filter manager
        for topic, selected in self._current_selections.items():
            if selected:
                self.filter_manager.add_topic_filter(topic)
            else:
                self.filter_manager.remove_topic_filter(topic)

        # Return the current selections
        self.dismiss(self._current_selections)

    def action_cancel(self) -> None:
        """Cancel changes and close the dialog."""
        # Restore original selections
        for topic in self._current_selections:
            original_selected = topic in self._initial_selected_topics
            self.filter_manager.remove_topic_filter(topic)
            if original_selected:
                self.filter_manager.add_topic_filter(topic)

        # Return None to indicate cancellation
        self.dismiss(None)

    def on_key(self, event) -> None:  # type: ignore[override]
        """Handle key events."""
        if getattr(event, "key", "") == "escape":
            self.action_cancel()

    def get_filter_status(self) -> str:
        """Get current filter status for display."""
        return self.filter_manager.get_filter_status()

    def get_selected_topics_count(self) -> int:
        """Get the number of currently selected topics."""
        return sum(
            1 for selected in self._current_selections.values() if selected
        )

    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return any(self._current_selections.values())

    def add_topic_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Add a callback for topic toggle events - legacy compatibility."""
        pass

    def update_filter_manager(self, filter_manager: FilterManager) -> None:
        """Update the filter manager and refresh display - legacy compatibility."""
        self.filter_manager = filter_manager
        self.refresh_topics()

    # Legacy compatibility methods for existing tests
    def action_close_filter(self) -> None:
        """Close the filter panel - legacy compatibility."""
        self.action_cancel()
