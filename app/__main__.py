"""Package entrypoint for awesome-list-view.

Allows running `python -m app` to launch the TUI or regenerate cache.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
