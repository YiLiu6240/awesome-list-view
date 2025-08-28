"""Cache management for awesome list data.

This module handles cache generation, validation, and management
for the awesome-list-view application.
"""

import os
import time
from pathlib import Path

from app.funcs.json_generator import (
    generate_awesome_list_json,
    write_cache_file,
)
from app.funcs.settings_loader import (
    get_awesome_list_paths,
    get_exclude_tags,
)
from app.funcs.settings_loader import (
    validate_settings as validate_settings_func,
)


def update_cache() -> tuple[bool, list[str]]:
    """Update the awesome list cache from source files.

    Returns:
        Tuple of (success, error_messages)
    """
    try:
        # Get paths from settings
        awesome_list_paths = get_awesome_list_paths()

        if not awesome_list_paths:
            return False, ["No awesome list paths configured in settings"]

        # Get exclude tags from settings
        exclude_tags = []
        try:
            exclude_tags = get_exclude_tags()
        except Exception as e:
            # Continue without exclude tags if they can't be loaded
            print(f"Warning: Could not load exclude_tags: {e}")

        # Validate paths exist
        missing_paths = []
        for path in awesome_list_paths:
            if not Path(path).exists():
                missing_paths.append(f"File not found: {path}")

        if missing_paths:
            return False, missing_paths

        # Generate JSON with exclude tags
        json_data = generate_awesome_list_json(awesome_list_paths, exclude_tags)

        # Write cache file
        cache_path = get_cache_path()
        write_cache_file(json_data, cache_path)

        excluded_info = ""
        if exclude_tags:
            excluded_info = f" (excluded tags: {', '.join(exclude_tags)})"

        return True, [
            f"Cache updated successfully: {cache_path}{excluded_info}"
        ]

    except Exception as e:
        return False, [f"Error updating cache: {str(e)}"]


def get_cache_path() -> str:
    """Get the path to the cache file using XDG cache directory.

    Returns:
        Path to ~/.cache/awesome-list-view/awesome_list.json
    """
    # Use XDG_CACHE_HOME if set, otherwise ~/.cache
    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        cache_dir = Path(cache_home) / "awesome-list-view"
    else:
        cache_dir = Path.home() / ".cache" / "awesome-list-view"

    # Create directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)

    return str(cache_dir / "awesome_list.json")


def is_cache_stale(cache_path: str, source_paths: list[str]) -> bool:
    """Check if cache is older than any source files.

    Args:
        cache_path: Path to cache file
        source_paths: List of source file paths

    Returns:
        True if cache is stale or doesn't exist
    """
    if not Path(cache_path).exists():
        return True

    cache_mtime = Path(cache_path).stat().st_mtime

    for source_path in source_paths:
        source_file = Path(source_path)
        if source_file.exists():
            source_mtime = source_file.stat().st_mtime
            if source_mtime > cache_mtime:
                return True

    return False


def get_cache_info() -> dict:
    """Get information about the current cache.

    Returns:
        Dictionary with cache metadata
    """
    cache_path = get_cache_path()

    cache_file = Path(cache_path)

    if not cache_file.exists():
        return {
            "exists": False,
            "path": cache_path,
            "size": 0,
            "last_modified": None,
        }

    stat = cache_file.stat()

    return {
        "exists": True,
        "path": cache_path,
        "size": stat.st_size,
        "last_modified": time.ctime(stat.st_mtime),
    }


def validate_settings() -> list[str]:
    """Validate the settings configuration.

    Returns:
        List of validation error messages
    """
    return validate_settings_func()
