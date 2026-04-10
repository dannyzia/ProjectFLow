"""End-to-end integration tests for the complete project-flow workflow."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from project_flow import __version__
from project_flow.config import load_config
from project_flow.context import build_context
from project_flow.generators import cursor, kilo, void_gen, vscode, windsurf, zed
from project_flow.models import Artifact
from project_flow.tech_stack import parse as parse_tech_stack
from project_flow.constants import UNKNOWN
from project_flow.writer import ArtifactWriter

MODE_AGENTS = {
    "ask-mode": {
        "display_name": "Ask",
        "description": "Ask mode agent",
        "prompt_file": "",
        "readonly": True,
        "tools": [],
        "model": "gpt-4",
        "handoffs": [],
        "kilo": {"color": "blue"},
    },
    "coding-agent": {
        "display_name": "Edit",
        "description": "Edit mode agent",
        "prompt_file": "",
        "readonly": False,
        "tools": ["edit"],
        "model": "gpt-4",
        "handoffs": [],
        "kilo": {"color": "green"},
    },
    "orchestrator": {
        "display_name": "Agent",
        "description": "Agent mode agent",
        "prompt_file": "",
        "readonly": False,
        "tools": ["edit", "run/terminal"],
        "model": "gpt-4",
        "handoffs": [],
        "kilo": {"color": "purple"},
    },
}


class TestEndToEndVSCodeGeneration:
    """End-to-end tests for VS Code generation."""

    def test_full_vscode_generation_workflow(self, tmp_path: Path) -> None:
        """Test complete VS Code generation from config to files."""
        # Create a complete config file
        config_content = {
            "version": "1.0",
            "project": {
                "name": "E2E Test Project",
                "description": "End-to-end test project",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": ["docs/PRD.md"],
                "language_globs": {"Python": "**/*.py"},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [
                {"filename": "test.prompt.md", "content": "Test prompt content."}
            ],
            "skills": [
                {
                    "name": "testing",
                    "description": "Testing skill",
                    "content": "# Testing\n\nWrite tests.",
                }
            ],
            "agents": {
                **MODE_AGENTS,
                "test-agent": {
                    "display_name": "Test Agent",
                    "description": "A test agent",
                    "prompt_file": "config/agents/test-agent.md",
                    "readonly": False,
                    "tools": ["search/codebase", "edit"],
                    "model": "gpt-4",
                    "handoffs": [],
                    "kilo": {"color": "blue"},
                },
            },
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        agents_dir = tmp_path / "config" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "test-agent.md").write_text(
            "## Test Agent\n\nYou are a test agent.", encoding="utf-8"
        )

        # Create tech stack file
        tech_stack_content = """---
project_name: "E2E Test Project"
primary_language: "Python"
framework: "Flask"
---
# Tech Stack

## Overview
Test tech stack file.
"""
        (tmp_path / "Tech_Stack.md").write_text(tech_stack_content, encoding="utf-8")

        # Load and parse
        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        # Generate artifacts
        artifacts = vscode.generate(config, tech_stack, context)

        # Write artifacts
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        writer.write_all(artifacts)

        # Verify expected files exist
        assert (tmp_path / ".github" / "copilot-instructions.md").exists()
        assert (tmp_path / ".github" / "agents" / "test-agent.agent.md").exists()
        assert (tmp_path / ".github" / "skills" / "testing" / "SKILL.md").exists()
        assert (tmp_path / ".github" / "prompts" / "test.prompt.md").exists()
        assert (tmp_path / ".vscode" / "settings.json").exists()

        # Verify content
        instructions = (tmp_path / ".github" / "copilot-instructions.md").read_text(
            encoding="utf-8"
        )
        assert "## E2E Test Project Project-Specific Instructions" in instructions
        assert "E2E Test Project" in instructions
        assert f"Generated by project-flow v{__version__}" in instructions

        # Verify agent file
        agent_file = (
            tmp_path / ".github" / "agents" / "test-agent.agent.md"
        ).read_text(encoding="utf-8")
        assert "name: Test Agent" in agent_file
        assert "You are a test agent." in agent_file

        # Verify settings.json
        settings = json.loads(
            (tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )
        assert "github.copilot" in str(settings)

    def test_multiple_generators_with_stub_ide(self, tmp_path: Path) -> None:
        """Test that stub generators don't cause crashes."""
        # Create minimal config with multiple IDEs
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Multi IDE Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": True,
                "cursor": True,
                "windsurf": True,
                "zed": True,
                "void": True,
            },
            "prompts": [],
            "skills": [],
            "agents": dict(MODE_AGENTS),
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Test"\n---\n# Tech Stack\n', encoding="utf-8"
        )

        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        all_artifacts = []
        all_artifacts.extend(vscode.generate(config, tech_stack, context))
        all_artifacts.extend(kilo.generate(config, tech_stack, context))
        all_artifacts.extend(cursor.generate(config, tech_stack, context))
        all_artifacts.extend(windsurf.generate(config, tech_stack, context))
        all_artifacts.extend(zed.generate(config, tech_stack, context))
        all_artifacts.extend(void_gen.generate(config, tech_stack, context))

        # Only VS Code should produce artifacts (others are stubs)
        assert len(all_artifacts) > 0  # VS Code should generate something

        # Write should succeed
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        writer.write_all(all_artifacts)  # Should not crash

    def test_duplicate_path_last_write_wins(self, tmp_path: Path) -> None:
        """Test that when artifacts share the same path, the last one wins."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Dedup Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": dict(MODE_AGENTS),
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")
        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Test"\n---\n# Tech Stack\n', encoding="utf-8"
        )

        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        artifacts = [
            Artifact(path="test.txt", content="First", source="vscode"),
            Artifact(path="test.txt", content="Second", source="kilo"),
        ]

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)

        # write_all uses last-write-wins deduplication via dict
        writer.write_all(artifacts)

        # The file should contain "Second" (last writer wins)
        assert (tmp_path / "test.txt").read_text(encoding="utf-8") == "Second\n"


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_cli_scaffold_vscode_command(self, tmp_path: Path) -> None:
        """Test the full CLI scaffold command for VS Code."""
        # Create a simple config
        config_content = {
            "version": "1.0",
            "project": {
                "name": "CLI Test",
                "description": "CLI integration test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": {
                **MODE_AGENTS,
                "cli-agent": {
                    "display_name": "CLI Agent",
                    "description": "Test agent",
                    "prompt_file": "config/agents/cli-agent.md",
                    "readonly": False,
                    "tools": [],
                    "model": "gpt-4",
                    "handoffs": [],
                    "kilo": {"color": "gray"},
                },
            },
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        agents_dir = tmp_path / "config" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "cli-agent.md").write_text(
            "## CLI Agent\n\nTest.", encoding="utf-8"
        )

        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "CLI Test"\n---\n# Tech Stack\n',
            encoding="utf-8",
        )

        # Run CLI command
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "scaffold",
                "--repo",
                "owner/repo",
                "--config",
                str(config_file),
                "--output-root",
                str(tmp_path),
                "--project-name",
                "CLI Test",
                "--ides",
                "vscode",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Verify files were created
        assert (tmp_path / ".github" / "agents" / "cli-agent.agent.md").exists()

    def test_cli_validate_command_removed(self, tmp_path: Path) -> None:
        """Validate command was removed in favor of scaffold/analyze."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Validate Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": {},
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "validate",
                "--config",
                str(config_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "invalid choice: 'validate'" in result.stderr

    def test_cli_list_agents_command_removed(self, tmp_path: Path) -> None:
        """List-agents command was removed in favor of scaffold/analyze."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "List Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": {
                "agent-one": {
                    "display_name": "Agent One",
                    "description": "First",
                    "prompt_file": "agents/one.md",
                    "readonly": False,
                    "tools": [],
                    "model": "gpt-4",
                    "handoffs": [],
                    "kilo": {"color": "gray"},
                },
                "agent-two": {
                    "display_name": "Agent Two",
                    "description": "Second",
                    "prompt_file": "agents/two.md",
                    "readonly": False,
                    "tools": [],
                    "model": "gpt-4",
                    "handoffs": [],
                    "kilo": {"color": "gray"},
                },
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        # Create prompt files
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "one.md").write_text("## One\n\nTest.", encoding="utf-8")
        (agents_dir / "two.md").write_text("## Two\n\nTest.", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "list-agents",
                "--config",
                str(config_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "invalid choice: 'list-agents'" in result.stderr


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_missing_config_file_error(self, tmp_path: Path) -> None:
        """Test error handling for missing config file."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "scaffold",
                "--repo",
                "owner/repo",
                "--config",
                str(tmp_path / "nonexistent.yml"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_invalid_config_version_error(self, tmp_path: Path) -> None:
        """Test error handling for unsupported config version."""
        config_content = {"version": "99.0", "project": {}, "ides": {}, "agents": {}}
        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "scaffold",
                "--repo",
                "owner/repo",
                "--config",
                str(config_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Unsupported config version" in result.stderr

    def test_missing_required_config_sections(self, tmp_path: Path) -> None:
        """Test error handling for missing required config sections."""
        config_content = {"version": "1.0", "project": {}}
        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "project_flow.cli",
                "scaffold",
                "--repo",
                "owner/repo",
                "--config",
                str(config_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "missing required sections" in result.stderr


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    def test_regenerate_with_unchanged_files(self, tmp_path: Path) -> None:
        """Test that regenerating with unchanged content skips files."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Skip Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": {
                **MODE_AGENTS,
                "test-agent": {
                    "display_name": "Test Agent",
                    "description": "Test",
                    "prompt_file": "config/agents/test-agent.md",
                    "readonly": False,
                    "tools": [],
                    "model": "gpt-4",
                    "handoffs": [],
                    "kilo": {"color": "gray"},
                },
            },
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")

        agents_dir = tmp_path / "config" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "test-agent.md").write_text(
            "## Test Agent\n\nTest.", encoding="utf-8"
        )

        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Skip Test"\n---\n# Tech Stack\n',
        )

        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Skip Test"\n---\n# Tech Stack\n',
            encoding="utf-8",
        )

        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        # First generation
        writer1 = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifacts1 = vscode.generate(config, tech_stack, context)
        writer1.write_all(artifacts1)
        summary1 = writer1.get_summary()

        # Second generation (same config)
        writer2 = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifacts2 = vscode.generate(config, tech_stack, context)
        writer2.write_all(artifacts2)
        summary2 = writer2.get_summary()

        # First generation should create files
        assert "Files created:" in summary1
        assert int(summary1.split("Files created:")[1].split("\n")[0]) > 0

        # Second generation should skip unchanged files
        assert "Files skipped (unchanged):" in summary2
        assert int(summary2.split("Files skipped (unchanged):")[1].split("\n")[0]) > 0

    def test_generate_with_backup(self, tmp_path: Path) -> None:
        """Test that backups are created when updating files."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Backup Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": dict(MODE_AGENTS),
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")
        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Backup Test"\n---\n# Tech Stack\n',
        )

        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        writer1 = ArtifactWriter(output_root=tmp_path, backup=True, dry_run=False)
        artifacts1 = vscode.generate(config, tech_stack, context)
        writer1.write_all(artifacts1)

        # Modify a file manually
        instructions_file = tmp_path / ".github" / "copilot-instructions.md"
        original_content = instructions_file.read_text(encoding="utf-8")
        instructions_file.write_text("Modified content", encoding="utf-8")

        # Second generation with backup
        writer2 = ArtifactWriter(output_root=tmp_path, backup=True, dry_run=False)
        writer2.write_all(artifacts1)

        # Verify backup was created
        backup_files = list(
            (tmp_path / ".github").glob("copilot-instructions.md.bak.*")
        )
        assert len(backup_files) == 1

        # Verify backup contains the modified content (what was on disk before overwrite)
        assert backup_files[0].read_text(encoding="utf-8") == "Modified content"

        # Verify file was restored
        assert instructions_file.read_text(encoding="utf-8") == original_content


class TestCrossPlatformCompatibility:
    """Tests for cross-platform compatibility."""

    def test_line_endings_normalize_across_platforms(self, tmp_path: Path) -> None:
        """Test that line endings are normalized regardless of platform."""
        config_content = {
            "version": "1.0",
            "project": {
                "name": "Line Ending Test",
                "description": "Test",
                "tech_stack_file": "Tech_Stack.md",
                "output_root": ".",
                "planning_docs": [],
                "language_globs": {},
            },
            "ides": {
                "vscode": True,
                "kilo": False,
                "cursor": False,
                "windsurf": False,
                "zed": False,
                "void": False,
            },
            "prompts": [],
            "skills": [],
            "agents": dict(MODE_AGENTS),
            "ide_config": {
                "vscode": {
                    "mode_agents": {
                        "ask": "ask-mode",
                        "edit": "coding-agent",
                        "agent": "orchestrator",
                    }
                }
            },
        }

        config_file = tmp_path / "project-flow.yml"
        config_file.write_text(yaml.dump(config_content), encoding="utf-8")
        (tmp_path / "Tech_Stack.md").write_text(
            '---\nproject_name: "Line Ending Test"\n---\n# Tech Stack\n',
        )

        config = load_config(config_file)
        tech_stack = parse_tech_stack(tmp_path / "Tech_Stack.md")
        context = build_context(config, tech_stack)

        artifacts = vscode.generate(config, tech_stack, context)
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        writer.write_all(artifacts)

        # Verify all generated artifact files use LF line endings
        artifact_paths = {tmp_path / a.path for a in artifacts}
        for file_path in artifact_paths:
            if file_path.is_file() and not file_path.suffix == ".json":
                content = file_path.read_bytes()
                # Should not contain CRLF
                assert b"\r\n" not in content, f"File {file_path} contains CRLF"
                # Should contain LF
                assert b"\n" in content, f"File {file_path} contains no LF"
