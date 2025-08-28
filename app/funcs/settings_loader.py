"""Settings loader for TOML configuration files only.

This module loads application settings from TOML configuration files
following XDG lookup order.
"""

from pathlib import Path
from typing import Any


def load_settings(config_path: str | None = None) -> dict[str, Any]:
    """Load settings from TOML or Python configuration file.

    Args:
        config_path: Path to configuration file (defaults to auto-detect)

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If no configuration file is found
        ImportError: If required dependencies are missing
    """
    settings = {}

    # Auto-detect config file if not specified
    if config_path is None:
        # XDG config precedence
        xdg_path = (
            Path.home() / ".config" / "awesome-list-view" / "settings.toml"
        )
        if xdg_path.exists():
            config_path = str(xdg_path)
        else:
            raise FileNotFoundError(
                "No configuration file found. Expected settings.toml in "
                "~/.config/awesome-list-view/"
            )

    # TOML format only
    config_file = Path(config_path) if config_path else None
    if config_file and config_file.suffix == ".toml" and config_file.exists():
        try:
            import importlib

            try:
                tomllib = importlib.import_module("tomllib")
            except ModuleNotFoundError:
                tomllib = importlib.import_module("tomli")
            from types import ModuleType as _ModuleType

            assert isinstance(tomllib, _ModuleType)
        except ModuleNotFoundError as e:
            raise ImportError(
                "TOML support requires 'tomli' package. "
                "Install with: uv add tomli"
            ) from e

        try:
            with config_file.open("rb") as f:
                config = tomllib.load(f)  # type: ignore[attr-defined]
        except Exception as e:
            raise RuntimeError(
                f"Failed to parse TOML '{config_file}': {e}"
            ) from e

        if "awesome-list-view" in config:
            settings.update(config["awesome-list-view"])
        else:
            settings.update(config)

        return settings

    # If not TOML or missing, raise error
    raise FileNotFoundError(
        "No configuration file found. Expected a TOML file at the provided "
        "path or in XDG locations."
    )


def get_awesome_list_paths(config_path: str | None = None) -> list[str]:
    """Get the AWESOME_LIST_PATHS setting.

    Args:
        config_path: Path to configuration file

    Returns:
        List of awesome list file paths

    Raises:
        ValueError: If AWESOME_LIST_PATHS is not configured properly
    """
    try:
        settings = load_settings(config_path)
    except (FileNotFoundError, ImportError):
        return []

    paths = settings.get("AWESOME_LIST_PATHS", [])

    if not isinstance(paths, list):
        raise ValueError("AWESOME_LIST_PATHS must be a list")

    # Expand ~ in paths
    expanded_paths = [str(Path(path).expanduser()) for path in paths]
    return expanded_paths


def get_exclude_tags(config_path: str | None = None) -> list[str]:
    """Get the EXCLUDE_TAGS setting.

    Args:
        config_path: Path to configuration file

    Returns:
        List of tags to exclude from curation (defaults to empty list)

    Raises:
        ValueError: If EXCLUDE_TAGS is not configured properly
    """
    try:
        settings = load_settings(config_path)
    except (FileNotFoundError, ImportError):
        return []

    exclude_tags = settings.get("EXCLUDE_TAGS", [])

    if not isinstance(exclude_tags, list):
        raise ValueError("EXCLUDE_TAGS must be a list")

    # Ensure all tags are strings
    for tag in exclude_tags:
        if not isinstance(tag, str):
            raise ValueError(
                f"All exclude tags must be strings, got {type(tag)}"
            )

    return exclude_tags


def validate_settings(config_path: str | None = None) -> list[str]:
    """Validate the settings configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        List of validation error messages
    """
    errors = []

    try:
        settings = load_settings(config_path)
    except FileNotFoundError as e:
        errors.append(str(e))
        return errors
    except ImportError as e:
        errors.append(str(e))
        return errors
    except Exception as e:
        errors.append(f"Error loading configuration: {str(e)}")
        return errors

    # Validate AWESOME_LIST_PATHS
    awesome_list_paths = settings.get("AWESOME_LIST_PATHS")

    if awesome_list_paths is None:
        errors.append("AWESOME_LIST_PATHS not found in configuration")
    elif not isinstance(awesome_list_paths, list):
        errors.append("AWESOME_LIST_PATHS must be a list")
    elif not awesome_list_paths:
        errors.append("AWESOME_LIST_PATHS is empty")
    else:
        for path in awesome_list_paths:
            if not isinstance(path, str):
                errors.append(
                    f"Invalid path type: {type(path)} (should be string)"
                )
            elif not Path(path).expanduser().exists():
                errors.append(f"File not found: {path}")
            elif not path.endswith(".md"):
                errors.append(f"Not a markdown file: {path}")

    # Validate EXCLUDE_TAGS (optional setting)
    exclude_tags = settings.get("EXCLUDE_TAGS")
    if exclude_tags is not None:
        if not isinstance(exclude_tags, list):
            errors.append("EXCLUDE_TAGS must be a list")
        else:
            for tag in exclude_tags:
                if not isinstance(tag, str):
                    errors.append(
                        f"Invalid exclude tag type: {type(tag)} (should be string)"
                    )

    return errors
