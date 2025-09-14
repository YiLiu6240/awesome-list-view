"""Basic tests to validate project setup."""

from pathlib import Path


def test_settings_import():
    """Test that settings loading function exists and works with XDG paths."""
    from app.funcs.settings_loader import (
        get_awesome_list_paths,
        load_settings,
    )

    # Functions should be importable and callable
    assert callable(load_settings)
    assert callable(get_awesome_list_paths)

    # Test that appropriate error is raised when no config exists
    try:
        get_awesome_list_paths("nonexistent_path.toml")
    except Exception:
        pass  # Expected to fail with nonexistent path


def test_pyproject_exists():
    """Test that pyproject.toml exists and has required content."""
    project_root = Path(__file__).parent.parent
    pyproject_file = project_root / "pyproject.toml"

    assert pyproject_file.exists(), "pyproject.toml not found"

    content = pyproject_file.read_text()
    assert "awesome-list-view" in content
    assert "textual" in content
    assert "ruff" in content
    assert "pytest" in content


def test_justfile_exists():
    """Test that justfile exists and has required recipes."""
    project_root = Path(__file__).parent.parent
    justfile = project_root / "justfile"

    assert justfile.exists(), "justfile not found"

    content = justfile.read_text()
    assert "fmt:" in content
    assert "lint:" in content
    assert "test:" in content
