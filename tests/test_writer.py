"""Tests for writer.py module (ArtifactWriter)."""

import json

from pathlib import Path
from unittest.mock import patch

import pytest

from project_flow.models import Artifact
from project_flow.writer import ArtifactWriter


class TestArtifactWriterBasicFunctionality:
    """Test basic writer operations."""

    def test_write_new_file(self, tmp_path: Path) -> None:
        """Test writing a new file that doesn't exist."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="new/file.txt", content="Hello, World!", source="test")

        writer.write_all([artifact])

        result_file = tmp_path / "new" / "file.txt"
        assert result_file.exists()
        assert result_file.read_text(encoding="utf-8") == "Hello, World!\n"
        assert (
            writer.get_summary()
            == "Files created: 1\nFiles updated: 0\nFiles skipped (unchanged): 0\nDry-run (not written): 0"
        )

    def test_write_multiple_files(self, tmp_path: Path) -> None:
        """Test writing multiple files in one operation."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifacts = [
            Artifact(path="file1.txt", content="Content 1", source="test"),
            Artifact(path="file2.txt", content="Content 2", source="test"),
            Artifact(path="subdir/file3.txt", content="Content 3", source="test"),
        ]

        writer.write_all(artifacts)

        assert (tmp_path / "file1.txt").exists()
        assert (tmp_path / "file2.txt").exists()
        assert (tmp_path / "subdir" / "file3.txt").exists()
        assert (
            writer.get_summary()
            == "Files created: 3\nFiles updated: 0\nFiles skipped (unchanged): 0\nDry-run (not written): 0"
        )

    def test_skip_unchanged_file(self, tmp_path: Path) -> None:
        """Test that unchanged files are skipped on second write."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="Same content", source="test")

        # First write
        writer.write_all([artifact])
        summary1 = writer.get_summary()
        assert "Files created: 1" in summary1

        # Second write with same content
        writer.write_all([artifact])
        summary2 = writer.get_summary()
        assert "Files skipped (unchanged): 1" in summary2

    def test_update_existing_file(self, tmp_path: Path) -> None:
        """Test updating an existing file with different content."""
        # Create initial file
        initial_file = tmp_path / "test.txt"
        initial_file.write_text("Original content", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="Updated content", source="test")

        writer.write_all([artifact])

        assert initial_file.read_text(encoding="utf-8") == "Updated content\n"
        assert "Files updated: 1" in writer.get_summary()


class TestArtifactWriterBackup:
    """Test backup functionality."""

    def test_create_backup_on_update(self, tmp_path: Path) -> None:
        """Test that a timestamped backup is created when updating a file."""
        # Create initial file
        initial_file = tmp_path / "test.txt"
        initial_file.write_text("Original content", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=True, dry_run=False)
        artifact = Artifact(path="test.txt", content="Updated content", source="test")

        writer.write_all([artifact])

        # Find backup file
        backup_files = list(tmp_path.glob("test.txt.bak.*"))
        assert len(backup_files) == 1
        backup_file = backup_files[0]
        assert backup_file.read_text(encoding="utf-8") == "Original content"
        assert initial_file.read_text(encoding="utf-8") == "Updated content\n"

    def test_no_backup_when_disabled(self, tmp_path: Path) -> None:
        """Test that no backup is created when backup is disabled."""
        initial_file = tmp_path / "test.txt"
        initial_file.write_text("Original content", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="Updated content", source="test")

        writer.write_all([artifact])

        backup_files = list(tmp_path.glob("test.txt.bak.*"))
        assert len(backup_files) == 0


class TestArtifactWriterDryRun:
    """Test dry-run mode."""

    def test_dry_run_does_not_write_files(self, tmp_path: Path) -> None:
        """Test that dry-run mode logs actions without writing files."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=True)
        artifact = Artifact(path="test.txt", content="Content", source="test")

        writer.write_all([artifact])

        assert not (tmp_path / "test.txt").exists()
        assert "Dry-run (not written): 1" in writer.get_summary()

    def test_dry_run_with_multiple_artifacts(self, tmp_path: Path) -> None:
        """Test dry-run mode with multiple artifacts."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=True)
        artifacts = [
            Artifact(path="file1.txt", content="Content 1", source="test"),
            Artifact(path="file2.txt", content="Content 2", source="test"),
        ]

        writer.write_all(artifacts)

        assert not (tmp_path / "file1.txt").exists()
        assert not (tmp_path / "file2.txt").exists()
        assert "Dry-run (not written): 2" in writer.get_summary()


class TestArtifactWriterJSONMerge:
    """Test JSON merge functionality."""

    def test_json_merge_creates_new_file(self, tmp_path: Path) -> None:
        """Test JSON merge creates file if it doesn't exist."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"key1": "value1"}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        result = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        assert result == {"key1": "value1"}

    def test_json_merge_with_existing_file(self, tmp_path: Path) -> None:
        """Test JSON merge merges with existing file."""
        existing_file = tmp_path / "settings.json"
        existing_file.write_text('{"key1": "old1", "key2": "value2"}', encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"key1": "new1", "key3": "value3"}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        result = json.loads(existing_file.read_text(encoding="utf-8"))
        assert result["key1"] == "new1"  # Overwritten
        assert result["key2"] == "value2"  # Preserved
        assert result["key3"] == "value3"  # Added

    def test_json_merge_replaces_arrays(self, tmp_path: Path) -> None:
        """Test that JSON merge replaces arrays entirely."""
        existing_file = tmp_path / "settings.json"
        existing_file.write_text(
            '{"list": ["a", "b", "c"], "key": "keep"}', encoding="utf-8"
        )

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"list": ["x", "y"]}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        result = json.loads(existing_file.read_text(encoding="utf-8"))
        assert result["list"] == ["x", "y"]  # Replaced
        assert result["key"] == "keep"  # Preserved

    def test_json_merge_deep_merge_dicts(self, tmp_path: Path) -> None:
        """Test that JSON merge deep-merges nested dicts."""
        existing_file = tmp_path / "settings.json"
        existing_file.write_text(
            '{"nested": {"a": 1, "b": 2}, "key": "keep"}', encoding="utf-8"
        )

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"nested": {"b": 20, "c": 3}}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        result = json.loads(existing_file.read_text(encoding="utf-8"))
        assert result["nested"]["a"] == 1  # Preserved
        assert result["nested"]["b"] == 20  # Overwritten
        assert result["nested"]["c"] == 3  # Added
        assert result["key"] == "keep"

    def test_json_merge_invalid_existing_json(self, tmp_path: Path) -> None:
        """Test that invalid existing JSON is overwritten with warning."""
        existing_file = tmp_path / "settings.json"
        existing_file.write_text("invalid json content", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"new": "content"}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        result = json.loads(existing_file.read_text(encoding="utf-8"))
        assert result == {"new": "content"}

    def test_json_merge_validates_output(self, tmp_path: Path) -> None:
        """Test that JSON merge validates the output is valid JSON."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="settings.json",
            content='{"valid": "json"}',
            mode="json_merge",
            source="test",
        )

        writer.write_all([artifact])

        # Should not raise exception
        json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))


class TestArtifactWriterPathSecurity:
    """Test path security validation."""

    def test_reject_path_traversal_attack(self, tmp_path: Path) -> None:
        """Test that path traversal attacks are rejected."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="../../escape.txt", content="malicious", source="test")

        with pytest.raises(ValueError, match="Path escapes output root"):
            writer.write_all([artifact])

    def test_reject_absolute_path(self, tmp_path: Path) -> None:
        """Test that absolute paths outside output root are rejected."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="/etc/passwd", content="malicious", source="test")

        with pytest.raises(ValueError, match="Path escapes output root"):
            writer.write_all([artifact])

    def test_allow_normal_relative_paths(self, tmp_path: Path) -> None:
        """Test that normal relative paths are accepted."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="safe/path/file.txt", content="safe", source="test")

        writer.write_all([artifact])

        assert (tmp_path / "safe" / "path" / "file.txt").exists()

    def test_allow_dotdot_within_root(self, tmp_path: Path) -> None:
        """Test that '..' within the output root is resolved correctly."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        # Create a subdirectory first
        (tmp_path / "subdir").mkdir()

        # Path that goes up from subdir but stays within root
        artifact = Artifact(path="subdir/../file.txt", content="safe", source="test")

        writer.write_all([artifact])

        # Should be resolved to tmp_path/file.txt
        assert (tmp_path / "file.txt").exists()


class TestArtifactWriterNewlineNormalization:
    """Test newline normalization."""

    def test_normalize_crlf_to_lf(self, tmp_path: Path) -> None:
        """Test that CRLF line endings are normalized to LF."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="test.txt", content="line1\r\nline2\r\nline3", source="test"
        )

        writer.write_all([artifact])

        content = (tmp_path / "test.txt").read_text(encoding="utf-8")
        assert content == "line1\nline2\nline3\n"

    def test_normalize_cr_to_lf(self, tmp_path: Path) -> None:
        """Test that CR line endings are normalized to LF."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="test.txt", content="line1\rline2\rline3", source="test"
        )

        writer.write_all([artifact])

        content = (tmp_path / "test.txt").read_text(encoding="utf-8")
        assert content == "line1\nline2\nline3\n"

    def test_normalize_mixed_line_endings(self, tmp_path: Path) -> None:
        """Test that mixed line endings are normalized to LF."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="test.txt", content="line1\r\nline2\rline3\nline4", source="test"
        )

        writer.write_all([artifact])

        content = (tmp_path / "test.txt").read_text(encoding="utf-8")
        assert content == "line1\nline2\nline3\nline4\n"

    def test_skip_detection_with_different_line_endings(self, tmp_path: Path) -> None:
        """Test that files with only line ending differences are skipped."""
        # Create file with CRLF
        initial_file = tmp_path / "test.txt"
        initial_file.write_bytes(b"line1\r\nline2\r\n")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="line1\nline2\n", source="test")

        writer.write_all([artifact])

        # Should be skipped because content is logically the same
        assert "Files skipped (unchanged): 1" in writer.get_summary()


class TestArtifactWriterAtomicWrites:
    """Test atomic write functionality."""

    def test_failure_does_not_partial_write(self, tmp_path: Path) -> None:
        """Test that a failure during commit doesn't leave partial writes."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)

        # Write a valid artifact first
        valid_artifact = Artifact(
            path="valid.txt", content="valid content", source="test"
        )
        writer.write_all([valid_artifact])

        # Patch _commit to simulate a failure after staging
        with patch.object(
            writer, "_commit", side_effect=RuntimeError("Simulated failure")
        ):
            failing_artifacts = [
                Artifact(
                    path="will_fail.txt", content="should not appear", source="test"
                ),
            ]

            with pytest.raises(RuntimeError, match="Simulated failure"):
                writer.write_all(failing_artifacts)

        # Verify that valid file still exists and was not overwritten
        assert (tmp_path / "valid.txt").read_text(encoding="utf-8") == "valid content\n"

        # Verify that failing file was not created
        assert not (tmp_path / "will_fail.txt").exists()

    def test_staging_directory_cleanup(self, tmp_path: Path) -> None:
        """Test that staging directory is cleaned up after success."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="content", source="test")

        staging_dirs = []

        original_mkdtemp = __import__("tempfile").mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            staging_dirs.append(Path(d))
            return d

        with patch(
            "project_flow.writer.tempfile.mkdtemp", side_effect=tracking_mkdtemp
        ):
            writer.write_all([artifact])

        # Staging directory should be cleaned up
        for staging_dir in staging_dirs:
            assert not staging_dir.exists()


class TestArtifactWriterUTF8Encoding:
    """Test UTF-8 encoding handling."""

    def test_write_unicode_content(self, tmp_path: Path) -> None:
        """Test writing content with Unicode characters."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(
            path="test.txt",
            content="Hello 世界 🌍 Привет мир",
            source="test",
        )

        writer.write_all([artifact])

        content = (tmp_path / "test.txt").read_text(encoding="utf-8")
        assert content == "Hello 世界 🌍 Привет мир\n"

    def test_read_existing_unicode_file(self, tmp_path: Path) -> None:
        """Test reading existing file with Unicode content."""
        existing_file = tmp_path / "test.txt"
        existing_file.write_text("Existing 世界 🌍", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifact = Artifact(path="test.txt", content="New 世界 🌍", source="test")

        writer.write_all([artifact])

        content = existing_file.read_text(encoding="utf-8")
        assert content == "New 世界 🌍\n"


class TestArtifactWriterChangeLog:
    """Test change log tracking."""

    def test_change_log_tracks_all_actions(self, tmp_path: Path) -> None:
        """Test that change log tracks CREATE, UPDATE, and SKIP actions."""
        # Create an existing file
        (tmp_path / "existing.txt").write_text("old", encoding="utf-8")

        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        artifacts = [
            Artifact(path="new.txt", content="new", source="test"),  # CREATE
            Artifact(path="existing.txt", content="updated", source="test"),  # UPDATE
            Artifact(path="existing.txt", content="updated", source="test"),  # SKIP
        ]

        writer.write_all(artifacts)

        assert writer.change_log[0]["action"] == "CREATE"
        assert writer.change_log[0]["path"] == "new.txt"
        assert writer.change_log[1]["action"] == "UPDATE"
        assert writer.change_log[1]["path"] == "existing.txt"
        assert writer.change_log[2]["action"] == "SKIP"
        assert writer.change_log[2]["path"] == "existing.txt"

    def test_get_summary_formatting(self, tmp_path: Path) -> None:
        """Test that get_summary returns properly formatted summary."""
        writer = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)

        # Manually populate change log
        writer.change_log = [
            {"action": "CREATE", "path": "file1.txt"},
            {"action": "CREATE", "path": "file2.txt"},
            {"action": "UPDATE", "path": "file3.txt"},
            {"action": "SKIP", "path": "file4.txt"},
            {"action": "DRY-RUN", "path": "file5.txt"},
        ]

        summary = writer.get_summary()

        assert "Files created: 2" in summary
        assert "Files updated: 1" in summary
        assert "Files skipped (unchanged): 1" in summary
        assert "Dry-run (not written): 1" in summary


class TestArtifactWriterInstanceIsolation:
    """Test that writer instances are properly isolated."""

    def test_separate_change_logs(self, tmp_path: Path) -> None:
        """Test that separate writer instances have separate change logs."""
        writer1 = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)
        writer2 = ArtifactWriter(output_root=tmp_path, backup=False, dry_run=False)

        writer1.write_all(
            [Artifact(path="file1.txt", content="content", source="test")]
        )
        writer2.write_all(
            [Artifact(path="file2.txt", content="content", source="test")]
        )

        # Each writer should only track its own changes
        assert len(writer1.change_log) == 1
        assert len(writer2.change_log) == 1
        assert writer1.change_log[0]["path"] == "file1.txt"
        assert writer2.change_log[0]["path"] == "file2.txt"
