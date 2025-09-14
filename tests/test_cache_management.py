"""Tests for the unified cache management functionality."""

from unittest.mock import Mock, patch

import pytest

from app.app.cache_management import CacheManagementModal
from app.cli import AwesomeListApp


class TestCacheManagementModal:
    """Test the unified cache management modal functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.callback_called = False

        def mock_callback():
            self.callback_called = True

        self.modal = CacheManagementModal(app_callback=mock_callback)
        # Mock the log display widget
        self.modal.log_display = Mock()

    def test_cache_modal_initialization_with_callback(self):
        """Test that cache modal initializes with app callback."""

        def test_callback():
            pass

        modal = CacheManagementModal(app_callback=test_callback)

        assert modal.app_callback == test_callback
        assert modal.cache_status == "Ready"
        assert len(modal.operation_log) == 0

    def test_cache_modal_initialization_without_callback(self):
        """Test that cache modal initializes without app callback."""
        modal = CacheManagementModal()

        assert modal.app_callback is None

    def test_button_press_close(self):
        """Test that close button dismisses the modal."""
        with patch.object(self.modal, "dismiss") as mock_dismiss:
            # Create a mock button event
            button = Mock()
            button.id = "close"
            event = Mock()
            event.button = button

            self.modal.on_button_pressed(event)

            mock_dismiss.assert_called_once()

    def test_button_press_refresh(self):
        """Test that refresh button calls quick_refresh."""
        with patch.object(self.modal, "quick_refresh") as mock_refresh:
            button = Mock()
            button.id = "refresh"
            event = Mock()
            event.button = button

            self.modal.on_button_pressed(event)

            mock_refresh.assert_called_once()

    def test_add_log_message(self):
        """Test that log messages are added correctly."""
        test_message = "Test log message"

        self.modal.add_log_message(test_message)

        assert len(self.modal.operation_log) == 1
        assert self.modal.operation_log[0] == test_message

    def test_add_log_message_limit(self):
        """Test that log messages are limited to 20 entries."""
        # Add 25 messages
        for i in range(25):
            self.modal.add_log_message(f"Message {i}")

        # Should only keep the last 20
        assert len(self.modal.operation_log) == 20
        assert self.modal.operation_log[0] == "Message 5"
        assert self.modal.operation_log[-1] == "Message 24"

    @patch("app.app.data_loader.DataLoader")
    def test_quick_refresh_success(self, mock_data_loader_class):
        """Test successful quick refresh operation."""
        # Mock DataLoader
        mock_data_loader = Mock()
        mock_data_loader.refresh_cache.return_value = (True, ["Cache loaded"])
        mock_data_loader_class.return_value = mock_data_loader

        self.modal.quick_refresh()

        # Check that callback was called
        assert self.callback_called
        assert self.modal.cache_status == "Cache refreshed"

        # Check log messages
        assert (
            "🔄 Quick refresh: reloading cache data..."
            in self.modal.operation_log
        )
        assert (
            "✅ Cache data reloaded successfully!" in self.modal.operation_log
        )
        assert "📱 Main app data refreshed" in self.modal.operation_log

    @patch("app.app.data_loader.DataLoader")
    def test_quick_refresh_failure(self, mock_data_loader_class):
        """Test failed quick refresh operation."""
        # Mock DataLoader
        mock_data_loader = Mock()
        mock_data_loader.refresh_cache.return_value = (False, ["Cache error"])
        mock_data_loader_class.return_value = mock_data_loader

        self.modal.quick_refresh()

        # Check that callback was NOT called
        assert not self.callback_called
        assert self.modal.cache_status == "Refresh failed"

        # Check log messages
        assert "❌ Cache refresh failed!" in self.modal.operation_log

    @patch("app.app.cache_management.update_cache")
    def test_regenerate_cache_success(self, mock_update_cache):
        """Test successful cache regeneration."""
        mock_update_cache.return_value = (True, ["Cache regenerated"])

        self.modal.regenerate_cache()

        # Check that callback was called
        assert self.callback_called
        assert self.modal.cache_status == "Cache is up to date"

        # Check log messages
        assert "🔄 Starting cache regeneration..." in self.modal.operation_log
        assert "✅ Cache regeneration successful!" in self.modal.operation_log
        assert "📱 Main app data refreshed" in self.modal.operation_log


class TestAwesomeListAppCacheIntegration:
    """Test cache management integration with the main app."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.app = AwesomeListApp()

    def test_cache_management_key_binding_exists(self):
        """Test that 'r' key is bound to cache management."""
        # Check that 'r' key is in bindings
        binding_keys = [binding[0] for binding in self.app.BINDINGS]
        assert "r" in binding_keys

        # Check that it maps to cache_management action
        cache_binding = next(
            (binding for binding in self.app.BINDINGS if binding[0] == "r"),
            None,
        )
        assert cache_binding is not None
        if cache_binding is not None:  # Type guard for linter
            assert cache_binding[1] == "cache_management"

    def test_refresh_cache_action_removed(self):
        """Test that action_refresh_cache method has been removed."""
        assert not hasattr(self.app, "action_refresh_cache")

    def test_action_cache_management_exists(self):
        """Test that action_cache_management method exists."""
        assert hasattr(self.app, "action_cache_management")

    @patch("app.cli.CacheManagementModal")
    def test_action_cache_management_creates_modal_with_callback(
        self, mock_modal_class
    ):
        """Test that cache management action creates modal with app callback."""
        mock_modal = Mock()
        mock_modal_class.return_value = mock_modal

        with patch.object(self.app, "push_screen") as mock_push_screen:
            with patch.object(self.app, "load_data") as mock_load_data:
                self.app.action_cache_management()

                # Check that modal was created with callback
                assert mock_modal_class.called
                call_kwargs = mock_modal_class.call_args[1]
                assert "app_callback" in call_kwargs

                # Test the callback function
                callback = call_kwargs["app_callback"]
                callback()
                assert mock_load_data.called

                # Check that modal was pushed to screen
                assert mock_push_screen.called

    @patch("app.cli.CacheManagementModal", None)
    def test_action_cache_management_handles_missing_modal(self):
        """Test that cache management handles missing modal gracefully."""
        with patch.object(self.app, "notify") as mock_notify:
            self.app.action_cache_management()

            assert mock_notify.called
