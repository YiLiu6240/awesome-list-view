"""Detail view widget for displaying complete awesome list item information.

This module provides a detailed view component that shows all available
information about a selected awesome list item including full description,
complete tags, sections, and metadata.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from app.funcs.editor_manager import EditorManager
from app.funcs.schema import AwesomeListItem
from app.funcs.url_manager import URLManager


class DetailView(Container):
    """Widget for displaying detailed information about an awesome list item."""

    BINDINGS = [
        ("o", "open_url", "Open URL"),
        ("e", "edit_item", "Edit item"),
    ]

    DEFAULT_CSS = """
    DetailView {
        border: $panel;
        height: 1fr;
        padding: 1;
        scrollbar-size: 1 1;
    }

    DetailView .empty-state {
        color: $panel;
        text-style: italic;
        text-align: center;
        margin: 5 0;
    }

    DetailView .detail-content {
        color: $text;
        padding: 1;
    }
    """

    def __init__(self, app=None):
        super().__init__()
        self.current_item: AwesomeListItem | None = None
        self.url_manager = URLManager()
        self.editor_manager = EditorManager(app)

    def compose(self) -> ComposeResult:
        """Compose the detail view."""
        yield Static(
            "Select an item from the list to view details",
            classes="empty-state",
        )

    def set_item(self, item: AwesomeListItem | None):
        """Set the item to display in detail view."""
        self.current_item = item
        # Use simple text-based display for now to avoid mounting issues
        self._update_content()

    def _update_content(self):
        """Update the content display using simple text rendering."""
        self.remove_children()

        if self.current_item is None:
            content = "Select an item from the list to view details"
            self.mount(Static(content, classes="empty-state"))
        else:
            item = self.current_item

            # Build content as text
            content_parts = []

            # Title
            content_parts.append(f"[bold accent]{item['title']}[/]")
            content_parts.append("")

            # Link
            if item["link"]:
                content_parts.append("[bold secondary]Link[/]")
                content_parts.append(f"[italic accent]{item['link']}[/]")
                content_parts.append("")

            # Description
            if item["description"].strip():
                content_parts.append("[bold secondary]Description[/]")
                content_parts.append(item["description"])
                content_parts.append("")

            # Tags
            if item["tags"]:
                content_parts.append("[bold secondary]Tags[/]")
                tag_text = " ".join(f"[dim]#{tag}[/]" for tag in item["tags"])
                content_parts.append(tag_text)
                content_parts.append("")

            # Sections
            if item["sections"]:
                content_parts.append("[bold secondary]Sections[/]")
                for section in item["sections"]:
                    content_parts.append(f"  • {section}")
                content_parts.append("")

            # Metadata
            content_parts.append("[bold secondary]Metadata[/]")
            content_parts.append(f"Tags: {len(item['tags'])}")
            content_parts.append(f"Sections: {len(item['sections'])}")
            content_parts.append(f"Has Link: {'Yes' if item['link'] else 'No'}")
            content_parts.append(
                f"Has Description: {'Yes' if item['description'].strip() else 'No'}"
            )

            content = "\n".join(content_parts)
            self.mount(Static(content, markup=True, classes="detail-content"))

    def get_current_item(self) -> AwesomeListItem | None:
        """Get the currently displayed item."""
        return self.current_item

    def action_open_url(self) -> None:
        """Open the URL of the currently displayed item."""
        if not self.current_item:
            self.notify("No item selected", severity="warning")
            return

        url = self.current_item.get("link", "").strip()
        if not url:
            self.notify("No URL available for this item", severity="warning")
            return

        success = self.url_manager.open_url(url)
        if success:
            self.notify(f"Opened: {url}", severity="information")
        else:
            error = self.url_manager.get_last_error()
            self.notify(f"Failed to open URL: {error}", severity="error")

    def action_edit_item(self) -> None:
        """Edit the currently displayed item in external text editor."""
        if not self.current_item:
            self.notify("No item selected for editing", severity="warning")
            return

        # Create a copy to avoid modifying the original
        item_copy = dict(self.current_item)  # type: ignore[assignment]

        self.notify("Opening item in editor...", severity="information")

        try:
            # Edit the item
            changes = self.editor_manager.edit_item(item_copy)  # type: ignore[arg-type]

            if changes:
                # Apply changes to the original item
                for key, value in changes.items():
                    if key in self.current_item:
                        self.current_item[key] = value

                self.notify("Item updated successfully", severity="information")

                # Refresh the display
                self.set_item(self.current_item)
            else:
                # No changes or cancelled
                self.notify(
                    "Edit cancelled or no changes made", severity="information"
                )

        except Exception as e:
            error = self.editor_manager.get_last_error()
            self.notify(
                f"Failed to edit item: {error or str(e)}", severity="error"
            )
