"""Tests for scanner.py module."""

import pytest

from project_flow.scanner import find_config_files, parse_repo_url


class TestParseRepoUrl:
    """Tests for GitHub repo URL parsing."""

    def test_parse_https_url(self):
        result = parse_repo_url("https://github.com/owner/repo")
        assert result["host"] == "github.com"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_https_url_with_git_suffix(self):
        result = parse_repo_url("https://github.com/owner/repo.git")
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_ssh_url(self):
        result = parse_repo_url("git@github.com:owner/repo.git")
        assert result["host"] == "github.com"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_ssh_url_without_git_suffix(self):
        result = parse_repo_url("git@github.com:owner/repo")
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_shorthand(self):
        result = parse_repo_url("owner/repo")
        assert result["host"] == "github.com"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_shorthand_with_git_suffix(self):
        result = parse_repo_url("owner/repo.git")
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_custom_host_https(self):
        result = parse_repo_url("https://gitlab.com/owner/repo")
        assert result["host"] == "gitlab.com"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"

    def test_parse_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Cannot parse repo URL"):
            parse_repo_url("not-a-valid-url")

    def test_parse_empty_url_raises(self):
        with pytest.raises(ValueError, match="Cannot parse repo URL"):
            parse_repo_url("")


class TestFindConfigFiles:
    """Tests for config file pattern matching."""

    def test_find_python_config_files(self):
        tree = [
            "src/main.py",
            "pyproject.toml",
            "requirements.txt",
            "README.md",
            "LICENSE",
            ".github/workflows/ci.yml",
        ]
        matched = find_config_files(tree)
        assert "pyproject.toml" in matched
        assert "requirements.txt" in matched
        assert "README.md" in matched
        assert "LICENSE" in matched
        assert ".github/workflows/ci.yml" in matched
        assert "src/main.py" not in matched

    def test_find_javascript_config_files(self):
        tree = [
            "src/index.ts",
            "package.json",
            "tsconfig.json",
            "vite.config.ts",
            "README.md",
        ]
        matched = find_config_files(tree)
        assert "package.json" in matched
        assert "tsconfig.json" in matched
        assert "vite.config.ts" in matched

    def test_find_config_files_in_subdirectory(self):
        tree = [
            "backend/pyproject.toml",
            "frontend/package.json",
            "docker-compose.yml",
        ]
        matched = find_config_files(tree)
        assert "backend/pyproject.toml" in matched
        assert "frontend/package.json" in matched
        assert "docker-compose.yml" in matched

    def test_empty_tree_returns_empty(self):
        matched = find_config_files([])
        assert matched == []

    def test_no_matching_files(self):
        tree = ["src/main.py", "src/utils.py", "assets/logo.png"]
        matched = find_config_files(tree)
        assert matched == []

    def test_docker_compose_patterns(self):
        tree = [
            "docker-compose.yml",
            "docker-compose.override.yml",
            "Dockerfile",
        ]
        matched = find_config_files(tree)
        assert "docker-compose.yml" in matched
        assert "Dockerfile" in matched
