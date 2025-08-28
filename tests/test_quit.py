"""Tests for application quit functionality."""

from unittest.mock import MagicMock, patch

import pytest

from app.cli import AwesomeListApp


class TestQuitFunctionality:
    """Test application quit functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = AwesomeListApp()

    def test_action_quit_app_calls_exit(self):
        """Test that action_quit_app calls self.exit()."""
        self.app.exit = MagicMock()

        self.app.action_quit_app()

        self.app.exit.assert_called_once()

    def test_action_quit_app_handles_exception(self):
        """Test that action_quit_app handles exceptions gracefully."""
        self.app.exit = MagicMock(side_effect=Exception("Test exception"))

        with pytest.raises(SystemExit) as exc_info:
            self.app.action_quit_app()

        assert exc_info.value.args[0] == 0

    def test_quit_bindings_exist(self):
        """Test that quit bindings are properly configured."""
        # Check that the BINDINGS include the quit actions
        binding_keys = [binding[0] for binding in self.app.BINDINGS]
        binding_actions = [binding[1] for binding in self.app.BINDINGS]

        assert "q" in binding_keys
        assert "ctrl+c" in binding_keys
        assert "quit_app" in binding_actions

    @patch("app.cli.parse_args")
    def test_main_handles_keyboard_interrupt(self, mock_parse_args):
        """Test that main() handles KeyboardInterrupt properly."""
        from app.cli import main

        # Mock parse_args to avoid CLI argument parsing
        mock_args = MagicMock()
        mock_args.regenerate_cache = False
        mock_parse_args.return_value = mock_args

        # Mock the app to raise KeyboardInterrupt
        with patch("app.cli.AwesomeListApp") as mock_app_class:
            mock_app = MagicMock()
            mock_app.run.side_effect = KeyboardInterrupt()
            mock_app_class.return_value = mock_app

            result = main()

            assert result == 1

    @patch("app.cli.parse_args")
    def test_main_handles_general_exception(self, mock_parse_args):
        """Test that main() handles general exceptions."""
        from app.cli import main

        # Mock parse_args to avoid CLI argument parsing
        mock_args = MagicMock()
        mock_args.regenerate_cache = False
        mock_parse_args.return_value = mock_args

        # Mock the app to raise a general exception
        with patch("app.cli.AwesomeListApp") as mock_app_class:
            mock_app = MagicMock()
            mock_app.run.side_effect = Exception("Test error")
            mock_app_class.return_value = mock_app

            with patch("builtins.print") as mock_print:
                result = main()

            assert result == 1
            mock_print.assert_called_once()

    def test_main_normal_execution(self):
        """Test that main() returns 0 on normal execution."""
        from app.cli import main

        # Mock successful execution
        with patch("app.cli.AwesomeListApp") as mock_app_class:
            mock_app = MagicMock()
            mock_app.run.return_value = None
            mock_app_class.return_value = mock_app

            with patch("app.cli.parse_args") as mock_parse_args:
                mock_args = MagicMock()
                mock_args.regenerate_cache = False
                mock_parse_args.return_value = mock_args

                result = main()

            assert result == 0
            mock_app.run.assert_called_once()


class TestAppInitialization:
    """Test application initialization for quit-related functionality."""

    def test_app_initialization(self):
        """Test that app initializes with correct default values."""
        app = AwesomeListApp()

        # Check that key attributes are initialized
        assert app.current_query == ""
        assert app.items == []
        assert app.all_items == []
        assert app.current_focus == "list"

    def test_app_bindings_configuration(self):
        """Test that app has proper binding configuration."""
        app = AwesomeListApp()

        # Verify BINDINGS is a list of tuples
        assert isinstance(app.BINDINGS, list)

        for binding in app.BINDINGS:
            assert isinstance(binding, tuple)
            assert len(binding) >= 2  # key, action, [description]

    def test_quit_app_action_exists(self):
        """Test that quit_app action method exists."""
        app = AwesomeListApp()

        # Check that the action method exists
        assert hasattr(app, "action_quit_app")
        assert callable(app.action_quit_app)


class TestKeyboardInterruptHandling:
    """Test handling of keyboard interrupts (Ctrl+C)."""

    def test_cli_main_keyboard_interrupt(self):
        """Test CLI main function handles KeyboardInterrupt."""
        from app.cli import main

        with patch("app.cli.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.regenerate_cache = False
            mock_parse.return_value = mock_args

            with patch("app.cli.AwesomeListApp") as mock_app_class:
                mock_app = MagicMock()
                mock_app_class.return_value = mock_app
                mock_app.run.side_effect = KeyboardInterrupt()

                result = main()

                assert result == 1

    def test_textual_app_keyboard_interrupt_during_run(self):
        """Test that keyboard interrupt during app.run() is handled."""
        app = AwesomeListApp()

        # Mock the run method to raise KeyboardInterrupt
        with patch.object(app, "run", side_effect=KeyboardInterrupt()):
            from app.cli import main

            with patch("app.cli.AwesomeListApp", return_value=app):
                with patch("app.cli.parse_args") as mock_parse:
                    mock_args = MagicMock()
                    mock_args.regenerate_cache = False
                    mock_parse.return_value = mock_args

                    result = main()

                    assert result == 1
