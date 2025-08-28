"""URL management functionality for opening links in browser.

This module provides cross-platform URL opening capabilities
with proper error handling and user feedback.
"""

import subprocess
import sys
import webbrowser


class URLManager:
    """Manages opening URLs in the system browser."""

    def __init__(self):
        """Initialize the URL manager."""
        self._last_error: str | None = None

    def open_url(self, url: str | None) -> bool:
        """Open a URL in the system browser.

        Args:
            url: The URL to open

        Returns:
            True if the URL was opened successfully, False otherwise
        """
        if not url or not isinstance(url, str):
            self._last_error = "Invalid URL provided"
            return False

        # Clean up the URL
        url = url.strip()
        if not url:
            self._last_error = "Empty URL provided"
            return False

        # Ensure URL has a scheme
        if not (url.startswith("http://") or url.startswith("https://")):
            if url.startswith("www."):
                url = f"https://{url}"
            elif "." in url:
                url = f"https://{url}"
            else:
                self._last_error = f"Invalid URL format: {url}"
                return False

        try:
            # Try using webbrowser module first (works on most platforms)
            success = webbrowser.open(url)
            if success:
                self._last_error = None
                return True

            # Fallback to platform-specific methods
            return self._open_with_system_command(url)

        except Exception as e:
            self._last_error = f"Failed to open URL: {e}"
            return False

    def _open_with_system_command(self, url: str) -> bool:
        """Try to open URL using system commands as fallback.

        Args:
            url: The URL to open

        Returns:
            True if successful, False otherwise
        """
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", url], check=True)
                return True
            elif sys.platform == "win32":  # Windows
                subprocess.run(["start", url], shell=True, check=True)
                return True
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", url], check=True)
                return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self._last_error = f"System command failed: {e}"
            return False

    def get_last_error(self) -> str | None:
        """Get the last error message.

        Returns:
            Last error message or None if no error
        """
        return self._last_error

    def is_valid_url(self, url: str | None) -> bool:
        """Check if a URL appears to be valid.

        Args:
            url: The URL to validate

        Returns:
            True if the URL appears valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False

        url = url.strip()
        if not url:
            return False

        # Basic URL validation
        if url.startswith("http://") or url.startswith("https://"):
            return "." in url
        elif url.startswith("www.") or "." in url:
            return True

        return False


def open_url_safe(url: str) -> tuple[bool, str | None]:
    """Convenience function to safely open a URL.

    Args:
        url: The URL to open

    Returns:
        Tuple of (success, error_message)
    """
    manager = URLManager()
    success = manager.open_url(url)
    error = manager.get_last_error()
    return success, error
