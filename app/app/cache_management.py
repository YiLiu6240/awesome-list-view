"""Cache management UI modal for enhanced cache operations.

This module provides a modal dialog for advanced cache management
operations like validation, diagnostics, and regeneration.
"""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

# Import cache management functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.funcs.cache_manager import (
    get_cache_path,
    update_cache,
    validate_settings,
)

# Constants
MAX_LOG_MESSAGES = 20


class CacheManagementModal(ModalScreen):
    """Modal screen for unified cache management operations."""

    CSS = """
    CacheManagementModal {
        align: center middle;
    }

    .cache-modal {
        width: 100;
        height: 60;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }

    .cache-modal-title {
        color: $primary;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    .cache-status {
        color: $text;
        margin: 1 0;
        padding: 1;
        border: solid $accent;
        background: $panel;
    }

    .cache-buttons {
        margin-top: 1;
        height: 6;
    }

    .cache-buttons Button {
        margin: 0 1;
        width: 20;
    }

    .cache-log {
        height: 10;
        border: solid $accent;
        padding: 1;
        background: $panel;
        scrollbar-size: 1 1;
    }
    """

    def __init__(self, app_callback=None):
        super().__init__()
        self.cache_status = "Ready"
        self.operation_log: list[str] = []
        self.app_callback = app_callback  # Callback to refresh main app data

    def compose(self) -> ComposeResult:
        """Compose the unified cache management modal."""
        with Container(classes="cache-modal"):
            yield Label("Cache Management", classes="cache-modal-title")

            yield Static(
                "Unified cache operations - reload, regenerate, and manage",
                classes="cache-status",
            )

            with Horizontal(classes="cache-buttons"):
                yield Button("Quick Refresh", id="refresh", variant="primary")
                yield Button(
                    "Validate Settings", id="validate", variant="default"
                )
                yield Button(
                    "Open in Editor", id="open_editor", variant="default"
                )

            with Horizontal(classes="cache-buttons"):
                yield Button(
                    "Regenerate Cache", id="regenerate", variant="success"
                )
                yield Button("View Status", id="status", variant="default")
                yield Button("Close", id="close", variant="error")

            # Log area for operation results
            self.log_display = Static(
                "Operations will be logged here...", classes="cache-log"
            )
            yield self.log_display

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the modal."""
        if event.button.id == "close":
            self.dismiss()
        elif event.button.id == "refresh":
            self.quick_refresh()
        elif event.button.id == "validate":
            self.validate_settings()
        elif event.button.id == "regenerate":
            self.regenerate_cache()
        elif event.button.id == "status":
            self.show_cache_status()
        elif event.button.id == "open_editor":
            self.open_cache_in_editor()

    def add_log_message(self, message: str) -> None:
        """Add a message to the operation log."""
        self.operation_log.append(message)
        # Keep only last MAX_LOG_MESSAGES messages
        if len(self.operation_log) > MAX_LOG_MESSAGES:
            self.operation_log = self.operation_log[-MAX_LOG_MESSAGES:]

        # Update display
        log_text = "\n".join(self.operation_log)
        self.log_display.update(log_text)

    def quick_refresh(self) -> None:
        """Quick refresh - reload cache data without regeneration."""
        # Import DataLoader locally to avoid circular imports
        from app.app.data_loader import DataLoader

        self.add_log_message("🔄 Quick refresh: reloading cache data...")

        try:
            data_loader = DataLoader()
            success, messages = data_loader.refresh_cache()

            if success:
                self.add_log_message("✅ Cache data reloaded successfully!")
                if messages:
                    for message in messages:
                        self.add_log_message(f"  i {message}")

                # Trigger app refresh if callback is available
                if self.app_callback:
                    self.app_callback()
                    self.add_log_message("📱 Main app data refreshed")

                self.cache_status = "Cache refreshed"
            else:
                self.add_log_message("❌ Cache refresh failed!")
                for message in messages:
                    self.add_log_message(f"  💥 {message}")
                self.cache_status = "Refresh failed"

        except ImportError as e:
            self.add_log_message(f"💥 Import error during refresh: {e}")
            self.cache_status = "Import error"
        except OSError as e:
            self.add_log_message(f"💥 File error during refresh: {e}")
            self.cache_status = "File error"

    def validate_settings(self) -> None:
        """Validate application settings."""
        self.add_log_message("🔍 Validating settings...")

        try:
            errors = validate_settings()

            if errors:
                self.add_log_message("❌ Settings validation failed:")
                for error in errors:
                    self.add_log_message(f"  • {error}")
                self.cache_status = "Settings have errors"
            else:
                self.add_log_message("✅ Settings are valid")
                self.cache_status = "Settings are valid"

        except ImportError as e:
            self.add_log_message(f"💥 Import error during validation: {e}")
            self.cache_status = "Import error"
        except OSError as e:
            self.add_log_message(f"💥 File error during validation: {e}")
            self.cache_status = "File error"

    def regenerate_cache(self) -> None:
        """Regenerate the awesome list cache."""
        self.add_log_message("🔄 Starting cache regeneration...")

        try:
            success, messages = update_cache()

            if success:
                self.add_log_message("✅ Cache regeneration successful!")
                for message in messages:
                    self.add_log_message(f"  📄 {message}")

                # Trigger app refresh if callback is available
                if self.app_callback:
                    self.app_callback()
                    self.add_log_message("📱 Main app data refreshed")

                self.cache_status = "Cache is up to date"
            else:
                self.add_log_message("❌ Cache regeneration failed!")
                for message in messages:
                    self.add_log_message(f"  💥 {message}")
                self.cache_status = "Cache regeneration failed"

        except ImportError as e:
            self.add_log_message(f"💥 Import error during regeneration: {e}")
            self.cache_status = "Import error"
        except OSError as e:
            self.add_log_message(f"💥 File error during regeneration: {e}")
            self.cache_status = "File error"

    def show_cache_status(self) -> None:
        """Show current cache status and information."""
        self.add_log_message("📊 Checking cache status...")

        try:
            cache_path = get_cache_path()
            cache_file = Path(cache_path)

            if cache_file.exists():
                # Get file info
                stat_info = cache_file.stat()
                file_size = stat_info.st_size

                mod_time = datetime.fromtimestamp(stat_info.st_mtime, tz=UTC)

                self.add_log_message(f"📁 Cache file exists: {cache_path}")
                self.add_log_message(f"📏 File size: {file_size:,} bytes")
                self.add_log_message(
                    f"🕒 Last modified: "
                    f"{mod_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )

                # Try to read and parse the cache
                try:
                    with cache_file.open(encoding="utf-8") as f:
                        data = json.load(f)

                    # Check cache format
                    if isinstance(data, dict) and "lists" in data:
                        # New format with metadata
                        lists = data["lists"]
                        metadata = data.get("metadata", {})
                        self.add_log_message(
                            "📊 Format: Enhanced (with metadata)"
                        )
                        self.add_log_message(
                            f"📚 Lists: {len(lists)}, "
                            f"Items: {metadata.get('total_items', 'unknown')}"
                        )
                    elif isinstance(data, list):
                        # Old format - list of awesome lists
                        total_items = sum(
                            len(lst.get("items", [])) for lst in data
                        )
                        self.add_log_message("📊 Format: Legacy (list only)")
                        self.add_log_message(
                            f"📚 Lists: {len(data)}, Items: {total_items}"
                        )
                    else:
                        self.add_log_message("❓ Unrecognized cache format")

                    self.cache_status = "Cache file is present"

                except json.JSONDecodeError:
                    self.add_log_message("💥 Cache file contains invalid JSON")

            else:
                self.add_log_message("📂 Cache file not found")
                self.cache_status = "No cache file found"

        except ImportError as e:
            self.add_log_message(f"💥 Import error checking status: {e}")
            self.cache_status = "Import error"
        except OSError as e:
            self.add_log_message(f"💥 File error checking status: {e}")
            self.cache_status = "File error"

    def open_cache_in_editor(self) -> None:
        """Open the cache file in $EDITOR."""
        self.add_log_message("📝 Opening cache file in editor...")

        try:
            cache_path = get_cache_path()

            # Check if cache file exists
            if not os.path.exists(cache_path):
                self.add_log_message(
                    "❌ Cache file does not exist. Generate cache first."
                )
                return

            # Get editor from environment
            editor = os.environ.get("EDITOR")
            if not editor:
                self.add_log_message("❌ $EDITOR environment variable not set")
                return

            # Open file in editor (suspend TUI temporarily)
            try:
                # Get the app instance to suspend it
                app = self.app
                with app.suspend():
                    subprocess.run([editor, cache_path], check=True)
                self.add_log_message(f"✅ Opened {cache_path} in {editor}")
            except subprocess.CalledProcessError as e:
                self.add_log_message(f"❌ Failed to open editor: {e}")
            except FileNotFoundError:
                self.add_log_message(f"❌ Editor '{editor}' not found")

        except ImportError:
            self.add_log_message("❌ Cache manager not available")
        except Exception as e:
            self.add_log_message(f"❌ Error opening cache file: {e}")

    def action_cancel(self) -> None:
        """Cancel the modal (ESC key binding)."""
        self.dismiss()
