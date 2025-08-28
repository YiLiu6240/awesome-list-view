"""Awesome List View TUI Application.

A textual-based terminal user interface for viewing and managing
awesome list items from markdown files.
"""

import argparse
import sys

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from app.app.cache_management import CacheManagementModal
from app.app.data_loader import DataLoader
from app.app.detail_view import DetailView
from app.app.layout import MainLayout
from app.app.list_view import AwesomeListView
from app.app.search_modal import SearchModal
from app.app.tag_filter import TagFilter
from app.app.topic_filter import TopicFilter
from app.funcs.filter_manager import FilterManager


class AwesomeListApp(App):
    """Main TUI application for awesome-list-view with search and filtering."""

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("ctrl+c", "quit_app", "Quit"),
        ("r", "cache_management", "Cache Management"),
        ("tab", "switch_pane", "Switch Pane"),
        ("s", "toggle_split", "Toggle Split View"),
        ("f", "open_tag_filter", "Tag Filter"),
        ("space", "open_tag_filter", "Tag Filter"),
        ("t", "open_topic_filter", "Topic Filter"),
        ("escape", "close_filter", "Close Filter"),
        ("slash", "focus_search", "Focus Search"),
        ("o", "open_url", "Open URL"),
        ("e", "edit_item", "Edit item"),
    ]

    def __init__(self):
        super().__init__()
        self.data_loader = None
        self.all_items = []
        self.items = []
        self.current_query = ""
        self.main_layout = None
        self.list_view = None
        self.detail_view = None
        self.tag_filter = None
        self.topic_filter = None
        self.filter_manager = None
        self.current_focus = "list"  # "list", "detail"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        if MainLayout is None:
            # Fallback layout if imports failed
            yield Header()
            yield Static(
                "Error: Could not load main layout components",
                id="error-message",
            )
            yield Footer()
            return

        self.main_layout = MainLayout()
        yield self.main_layout

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Awesome List View"
        self.sub_title = "TUI Dashboard for Awesome Lists"

        self.theme = "gruvbox"

        # Wait for layout to be fully mounted
        self.call_after_refresh(self.deferred_setup)

        # Schedule data loading with a longer delay to ensure UI is ready
        self.set_timer(1.0, self.load_data)

    def deferred_setup(self) -> None:
        """Setup views after layout is fully mounted."""
        # Initialize layout and primary panes when available
        if all(
            [
                MainLayout,
                AwesomeListView,
                DetailView,
            ]
        ):
            self.setup_split_view()

    def setup_split_view(self):
        """Setup the three-pane view with filter, list and detail views."""
        try:
            # Check if main layout is actually mounted and ready
            if not self.main_layout:
                self.update_status("Main layout not available")
                return

            # Create list and detail views
            if AwesomeListView is not None:
                self.list_view = AwesomeListView(app=self)
                # Get list view from main layout for configuration
                self.detail_view = DetailView(app=self)

            # Set up selection callback to update detail view
            if self.list_view:
                from app.funcs.schema import AwesomeListItem

                def _cb(index: int, item: AwesomeListItem | None) -> None:
                    self._on_list_selection_changed(index, item)

                self.list_view.add_selection_callback(_cb)

            # Get content area and set up views with safety checks
            content_area = self.main_layout.get_content_area()
            if not content_area:
                self.update_status("Content area not available")
                return

            # Try to find the containers before mounting
            try:
                # Probe required containers; presence is enough
                content_area.query_one("#list-pane")
                content_area.query_one("#detail-pane")
                content_area.query_one("#filter-pane")
            except Exception:
                # Containers don't exist yet, retry later
                self.set_timer(0.1, self.setup_split_view)
                return

            if content_area and self.list_view:
                content_area.set_list_view(self.list_view)
                # Set initial focus on list view after a short delay to ensure mounting is complete
                self.set_timer(
                    0.3,
                    lambda: self.list_view.focus() if self.list_view else None,
                )
            if content_area and self.detail_view:
                content_area.set_detail_view(self.detail_view)

        except Exception as e:
            self.update_status(f"Error setting up views: {str(e)}")

    def setup_filter_manager(self):
        """Setup the filter manager."""
        # Check if imports are available
        if not all([TagFilter, TopicFilter, FilterManager]):
            self.update_status("Filter components not available")
            return

        try:
            # Create filter manager even with empty items for better UX
            # This allows the filter interface to be available, showing "no items"
            items_to_use = self.items if self.items else []

            # Load exclude_tags from settings
            exclude_tags = []
            try:
                from app.funcs.settings_loader import get_exclude_tags

                exclude_tags = get_exclude_tags()
            except Exception as e:
                # If exclude_tags can't be loaded, continue with empty list
                self.update_status(f"Warning: Could not load exclude_tags: {e}")

            # Create filter manager with current items and exclude_tags
            if FilterManager is not None:
                self.filter_manager = FilterManager(items_to_use, exclude_tags)

            # Create tag filter widget for legacy compatibility
            if TagFilter is not None and self.filter_manager:
                self.tag_filter = TagFilter(self.filter_manager)

            # Create topic filter widget
            if TopicFilter is not None and self.filter_manager:
                self.topic_filter = TopicFilter(self.filter_manager)

            # Update status based on whether we have items
            if not self.items:
                self.update_status("Filter manager ready (no items loaded)")
            else:
                excluded_count = (
                    self.filter_manager.get_excluded_items_count()
                    if self.filter_manager
                    else 0
                )
                available_count = (
                    len(self.filter_manager.get_filtered_items())
                    if self.filter_manager
                    else len(self.items)
                )
                status_msg = (
                    f"Filter manager ready with {available_count} items"
                )
                if excluded_count > 0:
                    status_msg += f" ({excluded_count} excluded)"
                self.update_status(status_msg)

        except Exception as e:
            self.update_status(f"Error setting up filter: {str(e)}")
            # Clear filter manager on error
            self.filter_manager = None
            self.tag_filter = None
            self.topic_filter = None

    # Legacy search setup removed; replaced by simple modal-driven search

    def apply_search(self, query: str) -> None:
        """Apply a simple case-insensitive substring search over items."""
        query = query.strip()  # Strip whitespace to handle edge cases
        self.current_query = query
        if not query:
            self.clear_search()
            return
        q = query.lower()

        # Search over title, description, and tags
        from app.funcs.schema import AwesomeListItem

        def matches(item: AwesomeListItem) -> bool:
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()
            tags = " ".join(item.get("tags", [])).lower()
            return q in title or q in desc or q in tags

        result_items = [it for it in self.all_items if matches(it)]
        if self.filter_manager:
            self.filter_manager.set_search_results(result_items)
            self.filter_manager.set_search_query(query)
            final_items = self.filter_manager.get_filtered_items()
        else:
            final_items = result_items

        # Update items with search results
        self.items = final_items

        if self.list_view:
            self.list_view.set_items(final_items)
            try:
                self.list_view.clear_search_matches()
            except Exception:
                pass
        self._update_status_with_search()

    def clear_search(self) -> None:
        """Clear search and restore items through FilterManager if present."""
        self.current_query = ""
        if self.filter_manager:
            self.filter_manager.clear_search_results()
            final_items = self.filter_manager.get_filtered_items()
        else:
            final_items = self.all_items

        # Update items with cleared search results
        self.items = final_items

        if self.list_view:
            self.list_view.set_items(final_items)
            try:
                self.list_view.clear_search_matches()
            except Exception:
                pass
        self._update_status_with_search()

    def _update_status_with_search(self):
        """Update status bar with current search and filter information."""
        if not self.main_layout:
            return

        status_bar = self.main_layout.get_status_bar()

        if self.filter_manager:
            combined_status = self.filter_manager.get_combined_status()
        else:
            combined_status = f"Showing all {len(self.items)} items"

        # Get current selection from list view
        selected_item = None
        selected_index = -1
        if self.list_view:
            selected_item = self.list_view.get_selected_item()
            selected_index = self.list_view.selected_index

        # Update status bar
        if selected_item:
            status_bar.update_status(
                self.list_view.get_item_count() if self.list_view else 0,
                selected_index,
                selected_item.get("title", "Untitled"),
                combined_status,
            )
        else:
            status_bar.update_status(
                self.list_view.get_item_count() if self.list_view else 0,
                -1,
                "",
                combined_status,
            )

    def _on_filter_changed(self, tag: str, checked: bool):
        """Handle filter changes."""
        if not self.filter_manager:
            return

        # Get filtered items and update list view
        filtered_items = self.filter_manager.get_filtered_items()
        if self.list_view:
            self.list_view.set_items(filtered_items)

        # Update status bar with search and filter information
        self._update_status_with_search()

    def _on_list_selection_changed(self, index: int, item):
        """Handle list view selection changes."""
        # Update detail view with selected item
        if self.detail_view and item is not None:
            self.detail_view.set_item(item)

        # Update status bar
        if self.main_layout and self.list_view:
            status_bar = self.main_layout.get_status_bar()
            if item:
                status_bar.update_status(
                    self.list_view.get_item_count(),
                    index,
                    item.get("title", "Untitled"),
                )
            else:
                status_bar.update_status(self.list_view.get_item_count())

    def load_data(self):
        """Load data from cache file."""
        try:
            if DataLoader is None:
                self.update_status("Error: Could not import data loader")
                # Still setup filter manager even if DataLoader import failed
                self.setup_filter_manager()
                return

            self.data_loader = DataLoader()
            success, messages = self.data_loader.load_cache_data()

            if success:
                loaded_items = self.data_loader.get_all_items()
                self.all_items = loaded_items
                self.items = loaded_items.copy()
                self.update_status(f"Loaded {len(self.items)} items")

                # Debug: Check if we actually have items
                if len(self.items) > 0:
                    self.update_status(
                        f"First item: {self.items[0].get('title', 'No title')[:20]}..."
                    )
                else:
                    self.update_status("No items loaded from cache")

                # Update list view with items
                if self.list_view:
                    self.list_view.set_items(self.items)
                    # Set focus on the list view after items are loaded
                    self.call_after_refresh(
                        lambda: self.list_view.focus()
                        if self.list_view
                        else None
                    )

                # Re-apply current search if any, now that items are loaded
                if getattr(self, "current_query", ""):
                    self.apply_search(self.current_query)
            else:
                error_msg = "; ".join(messages)
                self.update_status(f"Error loading cache: {error_msg}")
                # Ensure we have empty lists for consistency
                self.all_items = []
                self.items = []
                # Still try to set focus on the list view for navigation
                if self.list_view:
                    self.call_after_refresh(
                        lambda: self.list_view.focus()
                        if self.list_view
                        else None
                    )

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            # Ensure we have empty lists for consistency
            self.all_items = []
            self.items = []
            # Still try to set focus on the list view for navigation
            if self.list_view:
                self.call_after_refresh(
                    lambda: self.list_view.focus() if self.list_view else None
                )

        # Always setup filter manager AFTER data loading, with correct items
        # This ensures the filter interface has the right data from startup
        self.setup_filter_manager()

    def update_status(self, message: str):
        """Update the status bar."""
        try:
            if self.main_layout:
                status_bar = self.main_layout.get_status_bar()
                # Simple update - just show message
                status_bar.update_status(0, -1, "")
                status_bar.update(message)
        except Exception:
            pass

    def action_switch_pane(self) -> None:
        """Switch focus between list and detail panes."""
        if not all([self.list_view, self.detail_view]):
            return

        if self.current_focus == "list":
            self.current_focus = "detail"
            if self.detail_view:
                self.detail_view.focus()
        else:
            self.current_focus = "list"
            if self.list_view:
                self.list_view.focus()

    def action_open_tag_filter(self) -> None:
        """Open the tag filter modal dialog."""
        if not self.filter_manager:
            # Try to setup filter manager if it's not available
            self.setup_filter_manager()

            # If still not available, show helpful message
            if not self.filter_manager:
                self.notify(
                    "Filter not available - check data loading status",
                    severity="warning",
                )
                return
        else:
            # Ensure filter manager has the latest items
            if self.items:
                self.filter_manager.update_items(self.items)

        dialog = TagFilter(self.filter_manager)

        def _handle_result(result: dict[str, bool] | None) -> None:
            """Handle the tag filter dialog result."""
            if result is not None and self.filter_manager:
                # Update list view with filtered items
                filtered_items = self.filter_manager.get_filtered_items()
                if self.list_view:
                    self.list_view.set_items(filtered_items)
                # Update status bar with search and filter information
                self._update_status_with_search()

        self.push_screen(dialog, _handle_result)

    def action_open_topic_filter(self) -> None:
        """Open the topic filter modal dialog."""
        if not self.filter_manager:
            # Try to setup filter manager if it's not available
            self.setup_filter_manager()

            # If still not available, show helpful message
            if not self.filter_manager:
                self.notify(
                    "Filter not available - check data loading status",
                    severity="warning",
                )
                return
        else:
            # Ensure filter manager has the latest items
            if self.items:
                self.filter_manager.update_items(self.items)

        dialog = TopicFilter(self.filter_manager)

        def _handle_result(result: dict[str, bool] | None) -> None:
            """Handle the topic filter dialog result."""
            if result is not None and self.filter_manager:
                # Update list view with filtered items
                filtered_items = self.filter_manager.get_filtered_items()
                if self.list_view:
                    self.list_view.set_items(filtered_items)
                # Update status bar with search and filter information
                self._update_status_with_search()

        self.push_screen(dialog, _handle_result)

    def action_close_filter(self) -> None:
        """Close the filter panel - legacy compatibility."""
        # No-op for modal dialog approach
        pass

    def action_toggle_split(self) -> None:
        """Toggle between split-pane and single-pane view."""
        if self.main_layout:
            content_area = self.main_layout.get_content_area()
            content_area.toggle_split_view()

    def action_focus_search(self) -> None:
        """Open the search dialog to enter a query."""
        initial = getattr(self, "current_query", "") or ""
        dialog = SearchModal(initial)

        def _handle_result(result: str | None) -> None:
            # None means cancel/escape: do nothing
            if result is None:
                return
            # Empty string clears search; non-empty applies it
            if result.strip():
                self.apply_search(result.strip())
            else:
                self.clear_search()

        self.push_screen(dialog, _handle_result)

    def action_cache_management(self) -> None:
        """Open the unified cache management modal."""
        if CacheManagementModal:
            # Create callback to refresh app data after cache operations
            def refresh_app_data():
                self.update_status("Refreshing app data...")
                self.load_data()

            modal = CacheManagementModal(app_callback=refresh_app_data)
            self.push_screen(modal)
        else:
            self.notify("Cache management not available", severity="warning")

    def action_quit_app(self) -> None:
        """Exit the application cleanly."""
        try:
            self.exit()
        except Exception:
            raise SystemExit(0) from None

    def action_open_url(self) -> None:
        """Open the URL of the currently selected item."""
        # Delegate to the currently focused component
        if self.current_focus == "list" and self.list_view:
            self.list_view.action_open_url()
        elif self.current_focus == "detail" and self.detail_view:
            self.detail_view.action_open_url()
        elif self.list_view:
            # Fallback to list view if no specific focus
            self.list_view.action_open_url()
        else:
            self.notify("No item available to open URL", severity="warning")

    def action_edit_item(self) -> None:
        """Edit the currently selected item."""
        # Delegate to the currently focused component
        if self.current_focus == "list" and self.list_view:
            self.list_view.action_edit_item()
        elif self.current_focus == "detail" and self.detail_view:
            self.detail_view.action_edit_item()
        elif self.list_view:
            # Fallback to list view if no specific focus
            self.list_view.action_edit_item()
        else:
            self.notify("No item available for editing", severity="warning")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TUI dashboard for viewing awesome list items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ---- --help ----
    parser.add_argument(
        "--version",
        action="version",
        version="awesome-list-view 0.1.0",
    )

    # ---- --config ----
    parser.add_argument(
        "--config",
        type=str,
        help="Path to settings TOML file (default: XDG)",
        default=None,
    )

    # ---- --regenerate-cache ----
    parser.add_argument(
        "--regenerate-cache",
        action="store_true",
        help="Regenerate the awesome list cache and exit",
    )

    res = parser.parse_args()
    return res


def regenerate_cache_command() -> None:
    """Regenerate the awesome list cache."""
    try:
        from app.funcs.cache_manager import update_cache, validate_settings

        print("Validating settings...")
        settings_errors = validate_settings()
        if settings_errors:
            print("Settings validation errors:")
            for error in settings_errors:
                print(f"  - {error}")
            return

        print("Regenerating awesome list cache...")
        success, messages = update_cache()

        if success:
            print("\u2713 Cache regeneration successful!")
        else:
            print("\u2717 Cache regeneration failed!")

        for message in messages:
            print(f"  {message}")

    except ImportError as e:
        print(f"Error: Could not import cache manager: {e}")
    except Exception as e:
        print(f"Error: {e}")


def main() -> int | None:
    """Main entry point for the application."""
    try:
        args = parse_args()

        if args.regenerate_cache:
            regenerate_cache_command()
            return 0

        app = AwesomeListApp()
        app.run()
        return 0
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
