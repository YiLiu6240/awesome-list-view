"""Data loader and cache manager for the TUI application.

This module handles loading and validating data from the awesome_list.json
cache file, providing a clean interface for the TUI components.
"""

import json
import os
from pathlib import Path

from app.funcs.schema import (
    AwesomeList,
    AwesomeListItem,
    CacheMetadata,
)


class DataLoader:
    """Singleton class for managing cache data loading and validation."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._cache_data: list[AwesomeList] = []
        self._all_items: list[AwesomeListItem] = []
        self._cache_metadata: CacheMetadata | None = None

        # Import here to avoid circular imports
        from app.funcs.cache_manager import get_cache_path

        self._cache_path = get_cache_path()

        self._last_loaded = 0
        self._initialized = True

    def load_cache_data(self) -> tuple[bool, list[str]]:
        """Load and parse data from awesome_list.json cache file.

        Returns:
            Tuple of (success, error_messages)
        """
        try:
            success, errors = self.validate_cache_file(self._cache_path)
            if not success:
                return False, errors

            with open(self._cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            # Handle both old format (list) and new format (dict with metadata)
            if isinstance(cache_data, list):
                # Old format - list of AwesomeList objects
                lists_data = cache_data
                self._cache_metadata = None
            else:
                # New format - dict with metadata and lists
                lists_data = cache_data.get("lists", [])
                metadata = cache_data.get("metadata", {})
                self._cache_metadata = CacheMetadata(
                    topics=metadata.get("topics", []),
                    tags=metadata.get("tags", []),
                    total_items=metadata.get("total_items", 0),
                    total_lists=metadata.get("total_lists", 0),
                )

            # Validate and convert to typed data
            validated_data = []
            validation_errors = []

            for i, awesome_list_data in enumerate(lists_data):
                try:
                    # Validate required fields for AwesomeList
                    if "topic" not in awesome_list_data:
                        validation_errors.append(
                            f"List {i}: Missing 'topic' field"
                        )
                        continue

                    if "items" not in awesome_list_data:
                        validation_errors.append(
                            f"List {i}: Missing 'items' field"
                        )
                        continue

                    # Validate items
                    validated_items = []
                    for j, item_data in enumerate(awesome_list_data["items"]):
                        item_errors = self._validate_item(
                            item_data, f"List {i}, Item {j}"
                        )
                        if item_errors:
                            validation_errors.extend(item_errors)
                        else:
                            # Create AwesomeListItem
                            item: AwesomeListItem = {
                                "title": item_data.get("title", ""),
                                "link": item_data.get("link", ""),
                                "description": item_data.get("description", ""),
                                "tags": item_data.get("tags", []),
                                "sections": item_data.get("sections", []),
                                "topic": item_data.get(
                                    "topic", awesome_list_data["topic"]
                                ),
                                "source_file": item_data.get(
                                    "source_file",
                                    awesome_list_data.get(
                                        "source_file", "unknown"
                                    ),
                                ),
                                "line_number": item_data.get("line_number", 0),
                            }
                            validated_items.append(item)

                    # Create AwesomeList
                    awesome_list: AwesomeList = {
                        "topic": awesome_list_data["topic"],
                        "items": validated_items,
                        "source_file": awesome_list_data.get(
                            "source_file", "unknown"
                        ),
                    }
                    validated_data.append(awesome_list)

                except Exception as e:
                    validation_errors.append(f"List {i}: {str(e)}")

            if validation_errors:
                # Still load valid data, but report warnings
                self._cache_data = validated_data
                self._update_all_items()
                return True, validation_errors

            self._cache_data = validated_data
            self._update_all_items()
            self._last_loaded = Path(self._cache_path).stat().st_mtime

            return True, []

        except FileNotFoundError:
            return False, [f"Cache file not found: {self._cache_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in cache file: {str(e)}"]
        except Exception as e:
            return False, [f"Error loading cache: {str(e)}"]

    def validate_cache_file(self, file_path: str) -> tuple[bool, list[str]]:
        """Check file existence and basic validity.

        Args:
            file_path: Path to the cache file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not Path(file_path).exists():
            errors.append(f"Cache file does not exist: {file_path}")
            errors.append(
                "Run 'python -m app --regenerate-cache' to create cache"
            )
            return False, errors

        if not os.access(file_path, os.R_OK):
            errors.append(f"Cannot read cache file: {file_path}")
            errors.append("Check file permissions")
            return False, errors

        # Check if file is empty
        file_path_obj = Path(file_path)
        if file_path_obj.stat().st_size == 0:
            errors.append(f"Cache file is empty: {file_path}")
            return False, errors

        return True, []

    def _validate_item(self, item_data: dict, context: str) -> list[str]:
        """Validate a single awesome list item.

        Args:
            item_data: Raw item data
            context: Context string for error reporting

        Returns:
            List of validation error messages
        """
        errors = []
        required_fields = ["title"]

        for field in required_fields:
            if field not in item_data:
                errors.append(f"{context}: Missing required field '{field}'")

        # Validate types
        if "tags" in item_data and not isinstance(item_data["tags"], list):
            errors.append(f"{context}: 'tags' must be a list")

        if "sections" in item_data and not isinstance(
            item_data["sections"], list
        ):
            errors.append(f"{context}: 'sections' must be a list")

        return errors

    def _update_all_items(self):
        """Update the flattened list of all items."""
        self._all_items = []
        for awesome_list in self._cache_data:
            self._all_items.extend(awesome_list["items"])

    def get_all_items(self) -> list[AwesomeListItem]:
        """Get flattened list of all items from all awesome lists.

        Returns:
            List of all awesome list items
        """
        return self._all_items.copy()

    def get_item_count(self) -> int:
        """Get total count of items across all lists.

        Returns:
            Total number of items
        """
        return len(self._all_items)

    def get_awesome_lists(self) -> list[AwesomeList]:
        """Get all awesome lists.

        Returns:
            List of AwesomeList objects
        """
        return self._cache_data.copy()

    def is_cache_fresh(self) -> bool:
        """Check if cache file has been modified since last load.

        Returns:
            True if cache is up to date
        """
        if not Path(self._cache_path).exists():
            return False

        current_mtime = Path(self._cache_path).stat().st_mtime
        return current_mtime <= self._last_loaded

    def refresh_cache(self) -> tuple[bool, list[str]]:
        """Refresh cache data from file.

        Returns:
            Tuple of (success, messages)
        """
        return self.load_cache_data()

    def get_cache_metadata(self) -> CacheMetadata | None:
        """Get cache metadata for filtering.

        Returns:
            CacheMetadata if available, None otherwise
        """
        return self._cache_metadata

    def get_available_topics(self) -> list[str]:
        """Get list of all available topics.

        Returns:
            List of topic names
        """
        if self._cache_metadata:
            return self._cache_metadata["topics"]

        # Fallback: extract topics from loaded data
        topics = set()
        for awesome_list in self._cache_data:
            topics.add(awesome_list["topic"])
        return sorted(topics)

    def get_available_tags(self) -> list[str]:
        """Get list of all available tags.

        Returns:
            List of tag names
        """
        if self._cache_metadata:
            return self._cache_metadata["tags"]

        # Fallback: extract tags from loaded data
        tags = set()
        for item in self._all_items:
            tags.update(item["tags"])
        return sorted(tags)

    def get_cache_info(self) -> dict:
        """Get information about the current cache state.

        Returns:
            Dictionary with cache metadata
        """
        return {
            "cache_path": self._cache_path,
            "exists": Path(self._cache_path).exists(),
            "item_count": self.get_item_count(),
            "list_count": len(self._cache_data),
            "last_loaded": self._last_loaded,
            "is_fresh": self.is_cache_fresh(),
        }
