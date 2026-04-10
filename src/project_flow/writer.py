"""ArtifactWriter for writing artifacts to disk with atomic staging, backup, and merge support."""

import json
import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from project_flow.constants import (
    BACKUP_SUFFIX,
    DEFAULT_ENCODING,
    JSON_INDENT,
    JSON_MERGE_MODE,
    STAGING_PREFIX,
    TIMESTAMP_FORMAT,
)
from project_flow.models import Artifact

logger = logging.getLogger(__name__)


class ArtifactWriter:
    """Writes Artifact objects to disk with atomic staging, timestamped backup, dry-run, and merge support."""

    def __init__(self, output_root: Path, backup: bool = True, dry_run: bool = False):
        """Initialize the ArtifactWriter.

        Args:
            output_root: The root directory where files will be written.
            backup: Whether to create timestamped backups before overwriting files.
            dry_run: If True, log what would be written without actually writing.
        """
        self.output_root = output_root.resolve()
        self.backup = backup
        self.dry_run = dry_run
        self.change_log: list[dict] = []  # Instance-level, NOT module-level

    def write_all(self, artifacts: list[Artifact]) -> None:
        """Write all artifacts to disk atomically via a staging directory.

        Args:
            artifacts: List of Artifact objects to write.
        """
        # Step 1: Handle dry-run mode
        if self.dry_run:
            for artifact in artifacts:
                self._dry_run_one(artifact)
            return

        # Step 2: Determine actions for each artifact in order
        # Track final version per path for staging, but log all actions
        final_artifacts: dict[
            str, tuple[Artifact, str]
        ] = {}  # path -> (artifact, content) for staging (dedup)
        artifact_sequence: dict[str, str] = {}  # path -> previous artifact content

        for artifact in artifacts:
            self._validate_path(artifact.path)
            content = self._normalize_content(artifact.content)
            full_path = self.output_root / artifact.path

            # Determine action for this artifact
            if artifact.path in artifact_sequence:
                # This is a duplicate artifact (seen before in this batch)
                prev_content = artifact_sequence[artifact.path]
                action = "SKIP" if prev_content == content else "UPDATE"
            elif full_path.exists():
                # File exists on disk, check if content changed
                try:
                    with open(full_path, "r", encoding=DEFAULT_ENCODING) as f:
                        existing_content = f.read()
                    existing_normalized = self._normalize_content(existing_content)
                    action = "SKIP" if existing_normalized == content else "UPDATE"
                except Exception:
                    action = "UPDATE"
            else:
                # File doesn't exist, will be CREATE
                action = "CREATE"

            # Log this artifact's action
            logger.info(f"[{action}] {artifact.path}")
            self.change_log.append({"action": action, "path": artifact.path})

            # Update tracking for duplicates and for staging
            artifact_sequence[artifact.path] = content
            final_artifacts[artifact.path] = (artifact, content)

        # Step 3: Create a temporary staging directory
        staging_dir = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX))

        try:
            # Step 4: Stage all final artifacts
            for path, (artifact, content) in final_artifacts.items():
                staged_path = staging_dir / path
                if artifact.mode == JSON_MERGE_MODE:
                    self._stage_json_merge(staged_path, artifact, content)
                else:
                    staged_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(
                        staged_path, "w", encoding=DEFAULT_ENCODING, newline=""
                    ) as f:
                        f.write(content)

            # Step 5: Commit all staged files to output_root
            self._commit(staging_dir, final_artifacts)
        except Exception as e:
            # Step 6: Log error and clean up staging directory on failure
            logger.error(f"Failed to write artifacts: {e}")
            shutil.rmtree(staging_dir, ignore_errors=True)
            raise
        finally:
            # Step 7: Clean up staging directory if it still exists
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

    def _validate_path(self, artifact_path: str) -> Path:
        """Validate that the artifact path stays inside output_root. Returns the resolved full path.

        Args:
            artifact_path: The relative path of the artifact.

        Returns:
            The resolved full path.

        Raises:
            ValueError: If the path escapes the output root.
        """
        # Step 1: Compute full path
        full_path = (self.output_root / artifact_path).resolve()

        # Step 2: Validate path stays inside output_root
        if not full_path.is_relative_to(self.output_root):
            raise ValueError(
                f"Path escapes output root: {artifact_path} resolves to {full_path} "
                f"which is outside {self.output_root}"
            )

        # Step 3: Return the validated full path
        return full_path

    def _normalize_content(self, content: str) -> str:
        """Normalize line endings to LF and ensure trailing newline.

        Args:
            content: The content to normalize.

        Returns:
            The content with all line endings normalized to LF and ending with a single newline.
        """
        # Step 1: Replace CRLF and CR with LF
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")

        # Step 2: Ensure trailing newline
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        elif not normalized:
            # Empty content should not have a newline
            pass

        return normalized

    def _dry_run_one(self, artifact: Artifact) -> None:
        """Log what would be written without writing anything.

        Args:
            artifact: The artifact to log.
        """
        # Step 1: Validate path
        self._validate_path(artifact.path)

        # Step 2: Log dry-run action
        logger.info(f"[DRY-RUN] Would write: {artifact.path}")

        # Step 3: Append to change log
        self.change_log.append({"action": "DRY-RUN", "path": str(artifact.path)})

    def _stage_json_merge(
        self, staged_path: Path, artifact: Artifact, content: str
    ) -> None:
        """Stage a JSON merge artifact. Reads existing file from output_root, merges, writes to staging.

        Args:
            staged_path: The path in the staging directory where the merged file will be written.
            artifact: The artifact containing the new JSON data.
            content: The new JSON content as a string.
        """
        # Step 1: Parse content as JSON
        new_data = json.loads(content)

        # Step 2: Compute real path in output_root
        real_path = self.output_root / artifact.path

        # Step 3: Merge with existing JSON if it exists
        if real_path.exists():
            try:
                with open(real_path, "r", encoding=DEFAULT_ENCODING) as f:
                    existing_data = json.load(f)

                # Deep-merge new_data into existing_data
                def deep_merge(existing, new):
                    """Recursively merge new dict into existing dict."""
                    for key, value in new.items():
                        if key in existing:
                            if isinstance(value, dict) and isinstance(
                                existing[key], dict
                            ):
                                deep_merge(existing[key], value)
                            else:
                                # For arrays and scalars, new_data wins
                                existing[key] = value
                        else:
                            # New key in new_data
                            existing[key] = value

                deep_merge(existing_data, new_data)
                merged = existing_data
            except json.JSONDecodeError:
                # Existing file is not valid JSON, log warning and use new_data only
                logger.warning(
                    f"Existing file is not valid JSON, overwriting: {real_path}"
                )
                merged = new_data
        else:
            # Step 4: File doesn't exist, use new_data
            merged = new_data

        # Step 5: Create parent directories
        staged_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 6: Write merged JSON to staging directory
        with open(staged_path, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(json.dumps(merged, indent=JSON_INDENT, ensure_ascii=False) + "\n")

    def _commit(
        self,
        staging_dir: Path,
        final_artifacts: dict[str, tuple[Artifact, str]],
    ) -> None:
        """Move all staged files to the real output_root with backup support.

        Note: Actions (CREATE/UPDATE/SKIP) are already logged in write_all(),
        so this method only writes files without duplicating action logging.

        Args:
            staging_dir: The staging directory containing all staged files.
            final_artifacts: Dict mapping path -> (artifact, content) for dedup.
        """
        # Step 1: Process each final artifact
        for path, (artifact, content) in final_artifacts.items():
            rel_path = Path(path)
            full_path = self.output_root / rel_path
            staged_file = staging_dir / rel_path

            # Step 2: Ensure staged file exists and read it
            if not staged_file.exists():
                continue

            with open(staged_file, "r", encoding=DEFAULT_ENCODING) as f:
                file_content = f.read()

            # Step 3: Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Step 4: If file exists and backup is enabled, create backup before overwriting
            if full_path.exists() and self.backup:
                self._backup(full_path, rel_path)

            # Step 5: Write the file
            with open(full_path, "w", encoding=DEFAULT_ENCODING, newline="") as f:
                f.write(file_content)

            # Step 6: POST-WRITE JSON VALIDATION for json_merge mode
            if full_path.suffix == ".json":
                try:
                    with open(full_path, "r", encoding=DEFAULT_ENCODING) as f:
                        json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"GENERATED INVALID JSON: {rel_path}")

    def _backup(self, full_path: Path, rel_path: Path) -> None:
        """Create a timestamped backup of an existing file before overwriting.

        Args:
            full_path: The full path to the file to back up.
            rel_path: The relative path for logging purposes.
        """
        # Step 1: Generate timestamp
        ts = datetime.now().strftime(TIMESTAMP_FORMAT)

        # Step 2: Create backup path with timestamp
        backup_path = full_path.with_suffix(full_path.suffix + f"{BACKUP_SUFFIX}{ts}")

        # Step 3: Copy file to backup location
        shutil.copy2(full_path, backup_path)

        # Step 4: Log backup action
        logger.info(f"[BACKUP] {rel_path} -> {rel_path}.bak.{ts}")

    def get_summary(self) -> str:
        """Return a formatted summary of all changes.

        Returns:
            A formatted string summarizing the changes.
        """
        # Step 1: Count actions
        created = sum(1 for e in self.change_log if e["action"] == "CREATE")
        updated = sum(1 for e in self.change_log if e["action"] == "UPDATE")
        skipped = sum(1 for e in self.change_log if e["action"] == "SKIP")
        dry_run = sum(1 for e in self.change_log if e["action"] == "DRY-RUN")

        # Step 2: Return formatted summary
        return (
            f"Files created: {created}\n"
            f"Files updated: {updated}\n"
            f"Files skipped (unchanged): {skipped}\n"
            f"Dry-run (not written): {dry_run}"
        )
