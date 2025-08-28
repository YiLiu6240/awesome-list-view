# Default recipe
default:
    @just --list --unsorted

# ==== Development ====

# Format code with ruff
[group('development')]
fmt:
    uv run ruff format .

# Lint code with ruff and ty
[group('development')]
lint:
    uv run ruff check --fix .
    uv run ty check .

# Run tests with pytest
[group('development')]
test:
    uv run pytest -vv

# Install dependencies
[group('development')]
install:
    uv sync --dev

# ==== Application ====

# Run the TUI application
[group('application')]
run:
    uv run python -m app
