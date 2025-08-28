"""Test configuration and fixtures for awesome-list-view tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_awesome_list():
    """Sample awesome list markdown content for testing."""
    return """---
tags:
  - llms
  - ai_tools
  - awesome
---

# Awesome list on large language models

______________________________________________________________________

## Models & Platforms #llms

- Gemma 3 #google #gemma

  <https://developers.googleblog.com/en/introducing-gemma-3-270m/>

  Google's latest small language model.

## LLM Coding Assistants #coding-assistants

- GitHub Copilot #github #coding

  <https://github.com/features/copilot>

  AI pair programmer by GitHub.

## Prompt Engineering #prompt-engineering

- LLM System Prompts

  <https://github.com/asgeirtj/system_prompts_leaks/>

  Collection of leaked system prompts from various LLM applications.
"""


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings file for testing."""
    settings_content = '''"""Test settings file."""
from typing import List

AWESOME_LIST_PATHS: List[str] = []
'''
    settings_file = tmp_path / "settings.py"
    settings_file.write_text(settings_content)
    return settings_file
