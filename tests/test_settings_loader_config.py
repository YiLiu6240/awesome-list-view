"""Tests for settings loader custom config and TOML errors."""

from pathlib import Path

from app.funcs.settings_loader import (
    get_awesome_list_paths,
    get_exclude_tags,
    validate_settings,
)


def test_custom_toml_config_path(tmp_path: Path):
    """Custom TOML path is respected and returns the configured file list."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "custom.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    paths = get_awesome_list_paths(str(cfg))
    assert paths == [str(sample_md)]


def test_exclude_tags_from_config(tmp_path: Path):
    """Test loading exclude_tags from TOML configuration."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
EXCLUDE_TAGS = ["deprecated", "legacy", "experimental"]
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "config_with_exclude.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    exclude_tags = get_exclude_tags(str(cfg))
    assert exclude_tags == ["deprecated", "legacy", "experimental"]


def test_exclude_tags_empty_from_config(tmp_path: Path):
    """Test loading empty exclude_tags from TOML configuration."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
EXCLUDE_TAGS = []
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "config_empty_exclude.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    exclude_tags = get_exclude_tags(str(cfg))
    assert exclude_tags == []


def test_exclude_tags_missing_from_config(tmp_path: Path):
    """Test that missing exclude_tags returns empty list."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "config_no_exclude.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    exclude_tags = get_exclude_tags(str(cfg))
    assert exclude_tags == []


def test_exclude_tags_invalid_type_validation(tmp_path: Path):
    """Test validation error when exclude_tags is not a list."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
EXCLUDE_TAGS = "deprecated"
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "config_invalid_exclude.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    errors = validate_settings(str(cfg))
    assert any("EXCLUDE_TAGS must be a list" in error for error in errors)


def test_exclude_tags_invalid_item_type_validation(tmp_path: Path):
    """Test validation error when exclude_tags contains non-string items."""
    sample_md = Path("tests/fixtures/sample_awesome_list.md")
    assert sample_md.exists()

    toml_content = """
AWESOME_LIST_PATHS = [
  "{path}"
]
EXCLUDE_TAGS = ["deprecated", 123, "legacy"]
""".strip().format(path=str(sample_md))

    cfg = tmp_path / "config_invalid_exclude_items.toml"
    cfg.write_text(toml_content, encoding="utf-8")

    errors = validate_settings(str(cfg))
    assert any("Invalid exclude tag type" in error for error in errors)


def test_toml_parse_error(tmp_path: Path):
    """Malformed TOML yields a clear validation error message."""
    bad_cfg = tmp_path / "bad.toml"
    # Missing closing bracket
    bad_cfg.write_text("AWESOME_LIST_PATHS = [ \n  'x.md'\n", encoding="utf-8")

    errors = validate_settings(str(bad_cfg))
    assert errors, "Expected errors for malformed TOML"
    # Ensure the message references configuration loading
    assert any(
        "Error loading configuration" in e or "TOML" in e for e in errors
    )
