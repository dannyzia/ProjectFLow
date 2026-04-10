"""Tests for tech_stack.py module."""

import tempfile
from pathlib import Path

import pytest

from project_flow.constants import UNKNOWN
from project_flow.models import TechStackData
from project_flow.tech_stack import parse as parse_tech_stack


class TestTechStackParser:
    """Test suite for Tech_Stack.md parsing functionality."""

    def test_parse_valid_tech_stack(self, tmp_path: Path) -> None:
        """Test parsing a complete Tech_Stack.md file."""
        tech_stack_content = """---
project_name: "Test Project"
project_description: "A test project for validation"
primary_language: "Python"
framework: "Flask"
database: "PostgreSQL"
package_manager: "pip"
test_framework: "pytest"
linting: "pylint"
formatting: "black"
typing: "mypy"
---

# Tech Stack

## Overview
This is a test tech stack file.
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        assert isinstance(result, TechStackData)
        assert result.project_name == "Test Project"
        assert result.project_description == "A test project for validation"
        assert result.primary_language == "Python"
        assert result.framework == "Flask"
        assert result.database == "PostgreSQL"
        assert result.package_manager == "pip"
        assert result.test_framework == "pytest"
        assert result.linting == "pylint"
        assert result.formatting == "black"
        assert result.typing == "mypy"

    def test_parse_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        """Test that missing file returns default TechStackData."""
        missing_file = tmp_path / "NonExistent.md"

        result = parse_tech_stack(missing_file)

        assert result.project_name == UNKNOWN
        assert result.project_description == UNKNOWN
        assert result.primary_language == UNKNOWN
        assert result.framework == UNKNOWN
        assert result.database == UNKNOWN

    def test_parse_global_coding_rules(self, tmp_path: Path) -> None:
        """Test parsing global coding rules section."""
        tech_stack_content = """---
project_name: "Test"
---

## Global Coding Rules
- Always use type hints
- Keep functions under 50 lines
- Write docstrings for all public functions
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        assert len(result.global_coding_rules) == 3
        assert "Always use type hints" in result.global_coding_rules
        assert "Keep functions under 50 lines" in result.global_coding_rules

    def test_parse_partial_yaml_with_defaults(self, tmp_path: Path) -> None:
        """Test parsing file with only some YAML fields."""
        tech_stack_content = """---
project_name: "Partial Project"
primary_language: "TypeScript"
---

# Tech Stack
Only partial YAML provided.
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        assert result.project_name == "Partial Project"
        assert result.primary_language == "TypeScript"
        assert result.project_description == UNKNOWN  # Default
        assert result.framework == UNKNOWN  # Default

    def test_parse_malformed_yaml(self, tmp_path: Path) -> None:
        """Test handling of malformed YAML frontmatter."""
        tech_stack_content = """---
project_name: "Test"
invalid_yaml: [unclosed array
---

# Tech Stack
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        # Should return defaults on YAML parse error
        assert result.project_name == UNKNOWN

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """Test parsing an empty file."""
        tech_stack_file = tmp_path / "Empty.md"
        tech_stack_file.write_text("")

        result = parse_tech_stack(tech_stack_file)

        assert result.project_name == UNKNOWN

    def test_parse_preserves_raw_content(self, tmp_path: Path) -> None:
        """Test that the raw markdown content is preserved."""
        tech_stack_content = """---
project_name: "Test"
---

# Tech Stack

## Frameworks
- Flask
- SQLAlchemy

## Deployment
Docker and Kubernetes.
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        assert "# Tech Stack" in result.raw_content
        assert "Flask" in result.raw_content
        assert "Docker and Kubernetes." in result.raw_content

    def test_parse_complex_global_rules(self, tmp_path: Path) -> None:
        """Test parsing global rules with multiple levels."""
        tech_stack_content = """---
project_name: "Test"
---

## Global Coding Rules
- **Code Style**: Follow PEP 8
  - Use 4 spaces for indentation
  - Maximum line length: 88 characters
- **Documentation**: All functions must have docstrings
- **Testing**: Test coverage must be > 80%
"""
        tech_stack_file = tmp_path / "Tech_Stack.md"
        tech_stack_file.write_text(tech_stack_content)

        result = parse_tech_stack(tech_stack_file)

        assert len(result.global_coding_rules) >= 3
        assert "**Code Style**: Follow PEP 8" in result.global_coding_rules
        assert "Use 4 spaces for indentation" in result.global_coding_rules
