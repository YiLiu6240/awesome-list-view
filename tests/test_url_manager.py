"""Unit tests for URL manager functionality."""

import subprocess
from unittest.mock import patch

from app.funcs.url_manager import URLManager, open_url_safe


class TestURLManager:
    """Test suite for URLManager class."""

    def test_initialization(self):
        """Test URLManager initialization."""
        manager = URLManager()
        assert manager.get_last_error() is None

    def test_invalid_url_validation(self):
        """Test validation of invalid URLs."""
        manager = URLManager()

        # Test empty and None URLs
        assert not manager.is_valid_url("")
        assert not manager.is_valid_url(None)
        assert not manager.is_valid_url("   ")

        # Test invalid URLs
        assert not manager.is_valid_url("not-a-url")
        assert not manager.is_valid_url("just text")

    def test_valid_url_validation(self):
        """Test validation of valid URLs."""
        manager = URLManager()

        # Test fully qualified URLs
        assert manager.is_valid_url("https://example.com")
        assert manager.is_valid_url("http://example.com")
        assert manager.is_valid_url("https://github.com/user/repo")

        # Test URLs without protocol
        assert manager.is_valid_url("www.example.com")
        assert manager.is_valid_url("example.com")
        assert manager.is_valid_url("github.com/user/repo")

    def test_url_normalization(self):
        """Test URL normalization during opening."""
        manager = URLManager()

        with patch("webbrowser.open") as mock_open:
            mock_open.return_value = True

            # Test that www URLs get https prefix
            manager.open_url("www.example.com")
            mock_open.assert_called_with("https://www.example.com")

            # Test that domain-only URLs get https prefix
            manager.open_url("example.com")
            mock_open.assert_called_with("https://example.com")

            # Test that full URLs are left unchanged
            manager.open_url("https://example.com")
            mock_open.assert_called_with("https://example.com")

    def test_successful_url_opening(self):
        """Test successful URL opening."""
        manager = URLManager()

        with patch("webbrowser.open") as mock_open:
            mock_open.return_value = True

            result = manager.open_url("https://example.com")

            assert result is True
            assert manager.get_last_error() is None
            mock_open.assert_called_once_with("https://example.com")

    def test_failed_webbrowser_opening(self):
        """Test fallback when webbrowser fails."""
        manager = URLManager()

        with patch("webbrowser.open") as mock_webbrowser:
            with patch.object(
                manager, "_open_with_system_command"
            ) as mock_system:
                mock_webbrowser.return_value = False
                mock_system.return_value = True

                result = manager.open_url("https://example.com")

                assert result is True
                mock_webbrowser.assert_called_once()
                mock_system.assert_called_once_with("https://example.com")

    def test_system_command_macos(self):
        """Test system command on macOS."""
        manager = URLManager()

        with patch("sys.platform", "darwin"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = None

                result = manager._open_with_system_command(
                    "https://example.com"
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["open", "https://example.com"], check=True
                )

    def test_system_command_windows(self):
        """Test system command on Windows."""
        manager = URLManager()

        with patch("sys.platform", "win32"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = None

                result = manager._open_with_system_command(
                    "https://example.com"
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["start", "https://example.com"], shell=True, check=True
                )

    def test_system_command_linux(self):
        """Test system command on Linux."""
        manager = URLManager()

        with patch("sys.platform", "linux"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = None

                result = manager._open_with_system_command(
                    "https://example.com"
                )

                assert result is True
                mock_run.assert_called_once_with(
                    ["xdg-open", "https://example.com"], check=True
                )

    def test_system_command_failure(self):
        """Test system command failure handling."""
        manager = URLManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

            result = manager._open_with_system_command("https://example.com")

            assert result is False
            assert "System command failed" in (manager.get_last_error() or "")

    def test_complete_failure_handling(self):
        """Test complete failure when all methods fail."""
        manager = URLManager()

        with patch("webbrowser.open") as mock_webbrowser:
            mock_webbrowser.return_value = False

            # Don't mock _open_with_system_command, let it run and fail naturally
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

                result = manager.open_url("https://example.com")

                assert result is False
                assert manager.get_last_error() is not None

    def test_invalid_url_error_handling(self):
        """Test error handling for invalid URLs."""
        manager = URLManager()

        # Test empty URL (after stripping whitespace)
        result = manager.open_url("   ")
        assert result is False
        assert "Empty URL" in (manager.get_last_error() or "")

        # Test None URL
        result = manager.open_url(None)
        assert result is False
        assert "Invalid URL" in (manager.get_last_error() or "")

        # Test invalid format
        result = manager.open_url("not-a-url")
        assert result is False
        assert "Invalid URL format" in (manager.get_last_error() or "")

    def test_exception_handling(self):
        """Test exception handling during URL opening."""
        manager = URLManager()

        with patch("webbrowser.open") as mock_open:
            mock_open.side_effect = Exception("Test exception")

            result = manager.open_url("https://example.com")

            assert result is False
            assert "Failed to open URL" in (manager.get_last_error() or "")
            assert "Test exception" in (manager.get_last_error() or "")


class TestConvenienceFunction:
    """Test suite for convenience functions."""

    def test_open_url_safe_success(self):
        """Test successful URL opening with convenience function."""
        with patch("webbrowser.open") as mock_open:
            mock_open.return_value = True

            success, error = open_url_safe("https://example.com")

            assert success is True
            assert error is None

    def test_open_url_safe_failure(self):
        """Test failed URL opening with convenience function."""
        with patch("webbrowser.open") as mock_open:
            mock_open.return_value = False

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

                success, error = open_url_safe("https://example.com")

                assert success is False
                assert error is not None
                assert "System command failed" in error

    def test_open_url_safe_invalid_url(self):
        """Test convenience function with invalid URL."""
        # Test with whitespace-only string (becomes empty after strip)
        success, error = open_url_safe("   ")

        assert success is False
        assert error is not None
        assert "Empty URL" in error
