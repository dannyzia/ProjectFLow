"""Shared test fixtures."""

from pathlib import Path

import pytest

from project_flow.constants import DEFAULT_CONFIG_FILENAME


@pytest.fixture
def project_root() -> Path:
    """Return the project-flow root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def config_path(project_root: Path) -> Path:
    """Return the path to project-flow.yml."""
    return project_root / DEFAULT_CONFIG_FILENAME
