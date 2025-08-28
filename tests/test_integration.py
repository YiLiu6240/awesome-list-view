"""Integration tests for the awesome list parsing pipeline."""

import json
import os
import tempfile

from app.funcs.json_generator import (
    generate_awesome_list_json,
    write_cache_file,
)
from app.funcs.markdown_parser import parse_awesome_list


def test_end_to_end_parsing():
    """Test complete parsing pipeline with sample fixture."""
    fixture_path = "tests/fixtures/sample_awesome_list.md"

    assert os.path.exists(fixture_path), f"Fixture not found: {fixture_path}"

    # Test markdown parsing
    awesome_list = parse_awesome_list(fixture_path)

    assert awesome_list["topic"] == "Awesome list on large language models"
    assert len(awesome_list["items"]) > 0

    # Verify first item has expected structure
    first_item = awesome_list["items"][0]
    required_fields = ["title", "link", "description", "tags", "sections"]
    for field in required_fields:
        assert field in first_item, f"Missing field: {field}"

    # Verify tag inheritance works
    assert "llms" in first_item["tags"]  # from frontmatter
    assert "models" in first_item["tags"]  # from section heading
    assert "google" in first_item["tags"]  # from item inline


def test_multiple_files_processing():
    """Test processing multiple awesome list files."""
    # Create a temporary second file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as tmp:
        tmp.write("""---
tags:
  - tools
  - development
---

# Awesome Development Tools

## Text Editors #editors

- VSCode #microsoft #editor

  <https://code.visualstudio.com/>

  Popular code editor by Microsoft.
""")
        tmp_path = tmp.name

    try:
        # Test with multiple files
        fixture_path = "tests/fixtures/sample_awesome_list.md"
        json_data = generate_awesome_list_json([fixture_path, tmp_path])

        # Parse JSON to verify structure
        parsed = json.loads(json_data)
        assert "lists" in parsed, "Expected 'lists' key in JSON structure"
        assert len(parsed["lists"]) == 2, (
            f"Expected 2 lists, got {len(parsed['lists'])}"
        )

        # Verify both topics are present
        topics = [lst["topic"] for lst in parsed["lists"]]
        assert "Awesome list on large language models" in topics
        assert "Awesome Development Tools" in topics

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


def test_cache_file_creation():
    """Test cache file creation and content validation."""
    fixture_path = "tests/fixtures/sample_awesome_list.md"

    # Generate JSON data
    json_data = generate_awesome_list_json([fixture_path])

    # Test cache file writing
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp:
        cache_path = tmp.name

    try:
        write_cache_file(json_data, cache_path)

        # Verify file was created
        assert os.path.exists(cache_path), "Cache file not created"

        # Verify content
        with open(cache_path) as f:
            cached_data = json.load(f)

        assert "lists" in cached_data, "Expected 'lists' key in cached data"
        assert len(cached_data["lists"]) == 1
        assert (
            cached_data["lists"][0]["topic"]
            == "Awesome list on large language models"
        )
        assert len(cached_data["lists"][0]["items"]) > 0

    finally:
        # Clean up
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def run_integration_tests():
    """Run all integration tests."""
    tests = [
        test_end_to_end_parsing,
        test_multiple_files_processing,
        test_cache_file_creation,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1

    print(f"\nIntegration Test Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    run_integration_tests()
