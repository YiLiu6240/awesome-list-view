# awesome-list-view

A TUI dashboard for viewing and managing awesome list items from markdown files.

This software is co-developed with AI agents using [opencode](https://github.com/sst/opencode).

## Overview

`awesome-list-view` is a terminal user interface that displays items from one or more user-provided "awesome list" markdown files. It provides visualization, filtering, searching, and editing capabilities for managing your curated lists of resources.

## Features

- **Visualization**: List view showing item titles and tags, detail view for descriptions
- **Filtering**: Filter items by tags and topics, including inherited tags from headings and frontmatter
- **Search**: Full-text search over item descriptions and tags with real-time highlighting
- **Navigation**: Browse URLs in your default browser
- **Editing**: Open items in your preferred text editor
- **Cache Management**: Automatic cache regeneration with manual control
- **Accessibility**: Icon-free interface with keyboard-only navigation

## Installation

- Clone the repository and install:

  ```bash
  git clone https://github.com/YiLiu6240/awesome-list-view
  cd awesome-list-view
  uv sync
  ```

- Install as a tool (optional, `-e` for editable):

  ```bash
  uv tool install -e <path-to-repo>
  ```

For development setup and detailed commands, see @DEV.md.

## Configuration

Create `~/.config/awesome-list-view/settings.toml` with your awesome list files:

```toml
AWESOME_LIST_PATHS = [
  "/path/to/awesome-list-1.md",
  "/path/to/awesome-list-2.md",
]

# Optional: exclude items with these tags
EXCLUDE_TAGS = ["deprecated", "legacy"]
```

For detailed configuration options and XDG paths, see @DEV.md.

## Usage

Run the application:

```bash
uv run awesome-list-view
# or with custom config:
uv run python -m app --config path/to/settings.toml
```

For development commands and task runner usage, see @DEV.md.

## Key Bindings

- **Search**: `/` to open search dialog
- **Filtering**: `f` or `Space` for tag filter, `t` for topic filter
- **Navigation**: `Tab` to switch panes, `j`/`k` or arrows for movement
- **Actions**: `o` to open URLs, `e` to edit items
- **Cache**: `r` for cache management
- **Views**: `s` to toggle split view
- **Exit**: `q` or `Ctrl+C`

For detailed usage instructions and filtering modes, see @DEV.md.

## Architecture

For technical implementation details, codebase structure, and development guidelines, see @DEV.md.

## Awesome List Format

For markdown format specifications and tag inheritance rules, see @DEV.md.

### Example Structure

```markdown
---
tags: [llms, ai_tools, awesome]
---

# Awesome Large Language Models

## Models & Platforms #llms

- Gemma 3 #google #gemma
  <https://developers.googleblog.com/en/introducing-gemma-3-270m/>

## Coding Assistants #coding-assistants

- LLM System Prompts
  <https://github.com/asgeirtj/system_prompts_leaks/>
  Collection of leaked system prompts from various AI assistants.
```

Key concepts: topics from level-1 headings, items as bullet points with URLs, tag inheritance from headings and frontmatter.
