"""Tests for scanner.py module."""

import pytest

from project_flow.scanner import find_config_files, parse_repo_url, scan_local_project


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


class TestScanLocalProject:
    """Tests for scan_local_project() — local filesystem scanner."""

    def test_scan_returns_expected_shape(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_path / "README.md").write_text("# Test")
        result = scan_local_project(tmp_path)
        assert "path" in result
        assert "tree" in result
        assert "config_files" in result
        assert "file_contents" in result

    def test_scan_reads_config_files_from_disk(self, tmp_path):
        content = "[project]\nname = 'hello'"
        (tmp_path / "pyproject.toml").write_text(content)
        result = scan_local_project(tmp_path)
        assert "pyproject.toml" in result["file_contents"]
        assert result["file_contents"]["pyproject.toml"] == content

    def test_scan_excludes_node_modules(self, tmp_path):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.json").write_text("{}")
        (tmp_path / "package.json").write_text('{"name": "app"}')
        result = scan_local_project(tmp_path)
        assert "package.json" in result["file_contents"]
        assert "node_modules/package.json" not in result["file_contents"]

    def test_scan_excludes_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "pyproject.toml").write_text("[venv]")
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = scan_local_project(tmp_path)
        assert ".venv/pyproject.toml" not in result["file_contents"]
        assert "pyproject.toml" in result["file_contents"]

    def test_scan_excludes_git_dir(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[core]")
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = scan_local_project(tmp_path)
        assert ".git/config" not in result["file_contents"]

    def test_scan_path_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            scan_local_project(tmp_path / "does_not_exist")

    def test_scan_file_as_path_raises(self, tmp_path):
        f = tmp_path / "somefile.py"
        f.write_text("x = 1")
        with pytest.raises(ValueError):
            scan_local_project(f)

    def test_scan_tree_contains_relative_paths(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("pass")
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = scan_local_project(tmp_path)
        assert any("src/main.py" in p or "src\\main.py" in p for p in result["tree"])

    def test_scan_empty_directory_returns_empty_contents(self, tmp_path):
        result = scan_local_project(tmp_path)
        assert result["file_contents"] == {}
        assert result["tree"] == []
