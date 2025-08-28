"""Filter management for awesome list items.

This module provides filtering capabilities for awesome list items,
including tag-based filtering with AND/OR logic and text search integration.
"""

from enum import Enum

from .schema import AwesomeListItem


class FilterMode(Enum):
    """Filter mode for multiple selection (tags/topics)."""

    AND = "and"
    OR = "or"


class FilterManager:
    """Manages filtering state and logic for awesome list items."""

    def __init__(
        self,
        items: list[AwesomeListItem],
        exclude_tags: list[str] | None = None,
    ) -> None:
        """Initialize filter manager with list items.

        Args:
            items: List of awesome list items to filter
            exclude_tags: List of tags to exclude from curation (defaults to empty)
        """
        self._all_items = items
        self._exclude_tags = set(exclude_tags or [])
        # Filter out items with excluded tags
        self._items = self._filter_excluded_tags(items)
        self._selected_tags: set[str] = set()
        self._selected_topics: set[str] = set()
        self._filter_mode = FilterMode.OR
        self._tag_counts: dict[str, int] = {}
        self._topic_counts: dict[str, int] = {}
        self._filtered_items: list[AwesomeListItem] = self._items.copy()
        self._search_query = ""
        self._search_filtered_items: list[AwesomeListItem] = []

        # Build tag and topic counts on initialization
        self._build_tag_counts()
        self._build_topic_counts()

    def _filter_excluded_tags(
        self, items: list[AwesomeListItem]
    ) -> list[AwesomeListItem]:
        """Filter out items that have any excluded tags.

        Args:
            items: List of items to filter

        Returns:
            List of items without any excluded tags
        """
        if not self._exclude_tags:
            return items

        filtered_items: list[AwesomeListItem] = []
        for item in items:
            item_tags = set(item["tags"])
            # Include item only if it has no excluded tags
            if not item_tags.intersection(self._exclude_tags):
                filtered_items.append(item)

        return filtered_items

    def _build_tag_counts(self) -> None:
        """Build tag counts from all items."""
        tag_counts = {}
        for item in self._items:
            for tag in item["tags"]:
                # Skip empty or whitespace-only tags
                if tag and tag.strip():
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        self._tag_counts = tag_counts

    def _build_topic_counts(self) -> None:
        """Build topic counts from all items."""
        topic_counts: dict[str, int] = {}
        for item in self._items:
            topic = item.get("topic", "Unknown") or "Unknown"
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        self._topic_counts = topic_counts

    def get_tag_counts(self) -> dict[str, int]:
        """Get dictionary of tag names to item counts.

        Returns:
            Dictionary mapping tag names to number of items with that tag
        """
        return self._tag_counts.copy()

    def get_available_tags(self) -> list[str]:
        """Get list of all available tags sorted alphabetically.

        Returns:
            Sorted list of tag names
        """
        return sorted(self._tag_counts.keys())

    def get_topic_counts(self) -> dict[str, int]:
        """Get dictionary of topic names to item counts."""
        return self._topic_counts.copy()

    def get_available_topics(self) -> list[str]:
        """Get list of all available topics sorted alphabetically."""
        return sorted(self._topic_counts.keys())

    def get_selected_topics(self) -> set[str]:
        """Get currently selected topics."""
        return self._selected_topics.copy()

    def add_topic_filter(self, topic: str) -> None:
        """Add a topic to the filter selection."""
        if topic in self._topic_counts:
            self._selected_topics.add(topic)
            self._update_filtered_items()

    def remove_topic_filter(self, topic: str) -> None:
        """Remove a topic from the filter selection."""
        self._selected_topics.discard(topic)
        self._update_filtered_items()

    def toggle_topic_filter(self, topic: str) -> None:
        """Toggle a topic in the filter selection."""
        if topic in self._selected_topics:
            self.remove_topic_filter(topic)
        else:
            self.add_topic_filter(topic)

    def get_selected_tags(self) -> set[str]:
        """Get currently selected tags.

        Returns:
            Set of selected tag names
        """
        return self._selected_tags.copy()

    def add_tag_filter(self, tag: str) -> None:
        """Add a tag to the filter selection.

        Args:
            tag: Tag name to add to filter
        """
        if tag in self._tag_counts:
            self._selected_tags.add(tag)
            self._update_filtered_items()

    def remove_tag_filter(self, tag: str) -> None:
        """Remove a tag from the filter selection.

        Args:
            tag: Tag name to remove from filter
        """
        self._selected_tags.discard(tag)
        self._update_filtered_items()

    def toggle_tag_filter(self, tag: str) -> None:
        """Toggle a tag in the filter selection.

        Args:
            tag: Tag name to toggle
        """
        if tag in self._selected_tags:
            self.remove_tag_filter(tag)
        else:
            self.add_tag_filter(tag)

    def clear_filters(self) -> None:
        """Clear all tag and topic filters."""
        self._selected_tags.clear()
        self._selected_topics.clear()
        self._update_filtered_items()

    def set_filter_mode(self, mode: FilterMode) -> None:
        """Set the filter mode for multiple tags.

        Args:
            mode: Filter mode (AND or OR)
        """
        self._filter_mode = mode
        self._update_filtered_items()

    def get_filter_mode(self) -> FilterMode:
        """Get current filter mode.

        Returns:
            Current filter mode
        """
        return self._filter_mode

    def toggle_filter_mode(self) -> None:
        """Toggle between AND and OR filter modes."""
        if self._filter_mode == FilterMode.AND:
            self.set_filter_mode(FilterMode.OR)
        else:
            self.set_filter_mode(FilterMode.AND)

    def set_search_results(self, search_results: list[AwesomeListItem]) -> None:
        """Set search results to filter from.

        Args:
            search_results: List of items from search results
        """
        self._search_filtered_items = search_results
        self._update_filtered_items()

    def clear_search_results(self) -> None:
        """Clear search results and return to tag-only filtering."""
        self._search_filtered_items = []
        self._search_query = ""
        self._update_filtered_items()

    def set_search_query(self, query: str) -> None:
        """Set the current search query for status display.

        Args:
            query: Search query string
        """
        self._search_query = query

    def get_search_query(self) -> str:
        """Get current search query.

        Returns:
            Current search query string
        """
        return self._search_query

    def _update_filtered_items(self) -> None:
        """Update the filtered items list based on current filters (search, topics, tags)."""
        # Start with search results if available, otherwise all items
        base_items = self._search_filtered_items or self._items

        # Apply topic filter first (items generally have a single topic)
        if self._selected_topics:
            # OR semantics for topics: include if item's topic is in selected topics
            topic_filtered: list[AwesomeListItem] = []
            selected_topics = self._selected_topics
            for item in base_items:
                topic = item.get("topic", "Unknown") or "Unknown"
                if topic in selected_topics:
                    topic_filtered.append(item)
            base_items = topic_filtered

        # Apply tag filters
        if not self._selected_tags:
            # No tag filters selected, use base items
            self._filtered_items = list(base_items)
            return

        filtered_items: list[AwesomeListItem] = []
        for item in base_items:
            item_tags = set(item["tags"])

            if self._filter_mode == FilterMode.AND:
                # AND mode: item must have ALL selected tags
                if self._selected_tags.issubset(item_tags):
                    filtered_items.append(item)
            else:
                # OR mode: item must have AT LEAST ONE selected tag
                if self._selected_tags.intersection(item_tags):
                    filtered_items.append(item)

        self._filtered_items = filtered_items

    def get_filtered_items(self) -> list[AwesomeListItem]:
        """Get the current filtered list of items.

        Returns:
            List of items matching current filter criteria
        """
        return self._filtered_items.copy()

    def get_filter_status(self) -> str:
        """Get human-readable filter status string including topics and tags."""
        base_count = (
            len(self._search_filtered_items)
            if self._search_filtered_items
            else len(self._items)
        )
        filtered_items = len(self._filtered_items)
        active_tag_filters = len(self._selected_tags)
        active_topic_filters = len(self._selected_topics)
        active_total = active_tag_filters + active_topic_filters

        # Build status message
        status_parts: list[str] = []

        # Base count info
        if self._search_query:
            if active_total == 0:
                status_parts.append(f"Showing {filtered_items} search results")
            else:
                status_parts.append(
                    f"Showing {filtered_items} of {base_count} search results"
                )
        else:
            if active_total == 0:
                status_parts.append(f"Showing all {filtered_items} items")
            else:
                status_parts.append(
                    f"Showing {filtered_items} of {base_count} items"
                )

        # Filter info
        if active_total > 0:
            filter_text = "filter" if active_total == 1 else "filters"
            if active_topic_filters > 0 and active_tag_filters > 0:
                status_parts.append(
                    f"({active_total} {filter_text} active: {active_topic_filters} topic, {active_tag_filters} tag)"
                )
            elif active_topic_filters > 0:
                status_parts.append(
                    f"({active_total} {filter_text} active: {active_topic_filters} topic)"
                )
            else:
                status_parts.append(
                    f"({active_total} {filter_text} active: {active_tag_filters} tag)"
                )

        return " ".join(status_parts)

    def has_active_filters(self) -> bool:
        """Check if any filters (tags or topics) are currently active."""
        return len(self._selected_tags) > 0 or len(self._selected_topics) > 0

    def has_search_results(self) -> bool:
        """Check if search results are currently active.

        Returns:
            True if search results are filtering the items
        """
        return bool(self._search_filtered_items)

    def update_items(self, items: list[AwesomeListItem]) -> None:
        """Update the items list and refresh filters.

        Args:
            items: New list of items to filter
        """
        self._all_items = items
        # Re-apply exclude tag filtering
        self._items = self._filter_excluded_tags(items)
        self._build_tag_counts()
        self._build_topic_counts()

        # Remove selected tags/topics that no longer exist
        valid_tags = set(self._tag_counts.keys())
        valid_topics = set(self._topic_counts.keys())
        self._selected_tags = self._selected_tags.intersection(valid_tags)
        self._selected_topics = self._selected_topics.intersection(valid_topics)

        # Clear search results since item list changed
        self._search_filtered_items = []
        self._search_query = ""

        # Update filtered items
        self._update_filtered_items()

    def get_exclude_tags(self) -> set[str]:
        """Get the current set of excluded tags.

        Returns:
            Set of excluded tag names
        """
        return self._exclude_tags.copy()

    def set_exclude_tags(self, exclude_tags: list[str]) -> None:
        """Set new exclude tags and refresh item filtering.

        Args:
            exclude_tags: List of tags to exclude from curation
        """
        self._exclude_tags = set(exclude_tags)
        # Re-filter all items with new exclude tags
        self._items = self._filter_excluded_tags(self._all_items)
        self._build_tag_counts()
        self._build_topic_counts()

        # Remove selected tags/topics that no longer exist
        valid_tags = set(self._tag_counts.keys())
        valid_topics = set(self._topic_counts.keys())
        self._selected_tags = self._selected_tags.intersection(valid_tags)
        self._selected_topics = self._selected_topics.intersection(valid_topics)

        # Clear search results since item list changed
        self._search_filtered_items = []
        self._search_query = ""

        # Update filtered items
        self._update_filtered_items()

    def get_total_items_count(self) -> int:
        """Get total number of items before exclude tag filtering.

        Returns:
            Total number of items in the original dataset
        """
        return len(self._all_items)

    def get_excluded_items_count(self) -> int:
        """Get number of items that were excluded due to exclude tags.

        Returns:
            Number of items filtered out by exclude tags
        """
        return len(self._all_items) - len(self._items)

    def get_filter_summary(self) -> tuple[int, int, int]:
        """Get filter summary statistics.

        Returns:
            Tuple of (total_items, filtered_items, active_filters)
        """
        return (
            len(self._items),
            len(self._filtered_items),
            len(self._selected_tags) + len(self._selected_topics),
        )

    def get_combined_status(self) -> str:
        """Get combined status including both search and filters (topics/tags)."""
        if self._search_query and self.has_active_filters():
            search_count = len(self._search_filtered_items)
            final_count = len(self._filtered_items)
            filter_count = len(self._selected_tags) + len(self._selected_topics)
            filter_text = "filter" if filter_count == 1 else "filters"
            return (
                f"Search: '{self._search_query}' b {search_count} results b "
                f"{final_count} items ({filter_count} {filter_text})"
            )
        elif self._search_query:
            return f"Search: '{self._search_query}' b {len(self._filtered_items)} results"
        elif self.has_active_filters():
            return self.get_filter_status()
        else:
            return f"Showing all {len(self._filtered_items)} items"
