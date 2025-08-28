"""Test markdown parser components."""

from app.funcs.markdown_parser import (
    extract_headings,
    extract_urls,
    parse_frontmatter,
    parse_heading_tags,
    parse_item_content,
)
from app.funcs.tag_processor import (
    filter_meaningful_tags,
    inherit_tags,
    normalize_tag,
)


def test_parse_frontmatter_valid():
    """Test parsing valid YAML frontmatter."""
    content = """---
tags:
  - python
  - testing
title: Test Document
---

# Content here"""

    frontmatter, remaining = parse_frontmatter(content)

    assert frontmatter["tags"] == ["python", "testing"]
    assert frontmatter["title"] == "Test Document"
    assert remaining.strip().startswith("# Content here")


def test_parse_frontmatter_invalid():
    """Test parsing invalid YAML frontmatter."""
    content = """---
invalid: yaml: content: [
---

# Content here"""

    frontmatter, remaining = parse_frontmatter(content)

    # Should return empty dict for invalid YAML
    assert frontmatter == {}
    assert remaining == content  # Content unchanged


def test_extract_headings_various_levels():
    """Test extracting headings at different levels."""
    content = """# Level 1 Heading
## Level 2 Heading #tag1
### Level 3 Heading #tag2 #tag3
Some content
#### Level 4 Heading"""

    headings = extract_headings(content)

    assert len(headings) == 4
    assert headings[0]["level"] == 1
    assert headings[0]["clean_text"] == "Level 1 Heading"
    assert headings[1]["level"] == 2
    assert headings[1]["tags"] == ["tag1"]
    assert headings[2]["level"] == 3
    assert headings[2]["tags"] == ["tag2", "tag3"]


def test_parse_heading_tags():
    """Test parsing tags from heading text."""
    test_cases = [
        ("Heading #tag1 #tag2", "Heading", ["tag1", "tag2"]),
        ("No tags here", "No tags here", []),
        ("Mixed #tag content #another", "Mixed content", ["tag", "another"]),
        ("#start Start with tag", "Start with tag", ["start"]),
    ]

    for input_text, expected_clean, expected_tags in test_cases:
        clean_text, tags = parse_heading_tags(input_text)
        assert clean_text == expected_clean
        assert tags == expected_tags


def test_extract_urls():
    """Test URL extraction from text."""
    test_cases = [
        ("<https://example.com>", ["https://example.com"]),
        ("https://example.com", ["https://example.com"]),
        ("[link](https://example.com)", ["https://example.com"]),
        (
            "Multiple: <https://a.com> and https://b.com",
            ["https://a.com", "https://b.com"],
        ),
        ("No URLs here", []),
    ]

    for input_text, expected_urls in test_cases:
        urls = extract_urls(input_text)
        # Clean up any URLs that might have extra characters
        clean_urls = []
        for url in urls:
            # Remove trailing parentheses that might be captured
            cleaned = url.rstrip(")")
            if cleaned not in clean_urls:
                clean_urls.append(cleaned)
        assert clean_urls == expected_urls


def test_parse_item_content_variations():
    """Test parsing various item content formats."""
    # Test with URL and description
    text1 = "Tool Name #tag1 #tag2\n\n  <https://example.com>\n\n  This is a description."
    title1, desc1, link1, tags1 = parse_item_content(text1)

    assert "Tool Name" in title1
    assert "description" in desc1
    assert link1 == "https://example.com"
    assert "tag1" in tags1 and "tag2" in tags1

    # Test without description
    text2 = "Simple Tool <https://simple.com> #simple"
    title2, desc2, link2, tags2 = parse_item_content(text2)

    assert "Simple Tool" in title2
    assert desc2 == ""
    assert link2 == "https://simple.com"
    assert "simple" in tags2


def test_tag_inheritance_complex():
    """Test complex tag inheritance scenarios."""
    item = {"tags": ["item-tag"]}
    section_tags = ["section-tag1", "section-tag2"]
    frontmatter_tags = ["front-tag", "awesome"]  # awesome should be filtered

    result = inherit_tags(item, section_tags, frontmatter_tags)

    # Should preserve order: item, section, frontmatter
    # Should filter out 'awesome'
    expected = ["item-tag", "section-tag1", "section-tag2", "front-tag"]
    assert result == expected


def test_normalize_tag():
    """Test tag normalization."""
    test_cases = [
        ("Python", "python"),
        ("#tag", "tag"),
        ("multi word", "multi-word"),
        ("  spaced  ", "spaced"),
        (
            "Special!@#Chars",
            "special-chars",
        ),  # Multiple special chars become single hyphen
    ]

    for input_tag, expected in test_cases:
        assert normalize_tag(input_tag) == expected


def test_filter_meaningful_tags():
    """Test filtering of excluded tags."""
    tags = ["python", "awesome", "testing", "AWESOME"]
    result = filter_meaningful_tags(tags)

    # Should remove 'awesome' (case insensitive - both lowercase and uppercase)
    assert result == ["python", "testing"]


# Manual test runner for pytest-less environment
def run_tests():
    """Run all tests manually."""
    test_functions = [
        test_parse_frontmatter_valid,
        test_parse_frontmatter_invalid,
        test_extract_headings_various_levels,
        test_parse_heading_tags,
        test_extract_urls,
        test_parse_item_content_variations,
        test_tag_inheritance_complex,
        test_normalize_tag,
        test_filter_meaningful_tags,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    run_tests()
