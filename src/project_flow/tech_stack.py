"""Tech stack parser for Project Flow."""

import logging
import tempfile
from pathlib import Path

import frontmatter

from project_flow.constants import DEFAULT_ENCODING, UNKNOWN
from project_flow.models import TechStackData

logger = logging.getLogger(__name__)


def parse(filepath: Path) -> TechStackData:
    """Parse a Tech_Stack.md file and return a TechStackData object. If file missing, return defaults.

    Args:
        filepath: Path to the Tech_Stack.md file.

    Returns:
        A TechStackData object with parsed data or defaults if file is missing.
    """
    # Step 1: Check if file exists
    if not filepath.exists():
        logger.warning(f"Tech stack file not found: {filepath}. Using defaults.")
        return default_data()

    # Step 2: Load the file with frontmatter
    try:
        post = frontmatter.load(str(filepath))
    except Exception:
        logger.warning(
            f"Failed to parse tech stack file (malformed YAML): {filepath}. Using defaults."
        )
        return default_data()

    # Step 3: Extract metadata and body
    metadata = post.metadata
    body = post.content

    # Step 4: Build TechStackData object
    return TechStackData(
        project_name=metadata.get("project_name", UNKNOWN),
        project_description=metadata.get("project_description", UNKNOWN),
        primary_language=metadata.get("primary_language", UNKNOWN),
        framework=metadata.get("framework", UNKNOWN),
        database=metadata.get("database", UNKNOWN),
        package_manager=metadata.get("package_manager", UNKNOWN),
        test_framework=metadata.get("test_framework", UNKNOWN),
        linting=metadata.get("linting", UNKNOWN),
        formatting=metadata.get("formatting", UNKNOWN),
        typing=metadata.get("typing", UNKNOWN),
        global_coding_rules=_parse_bullet_list(
            _extract_section(body, "Global Coding Rules")
        ),
        tech_stack_details=_extract_section(body, "Tech Stack Details"),
        raw_content=body,
    )


def parse_from_string(content: str) -> TechStackData:
    """Parse a Tech_Stack markdown string and return TechStackData.

    Uses the same parser behavior as parse(), but accepts raw file content.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding=DEFAULT_ENCODING, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        return parse(tmp_path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            logger.debug("Could not remove temporary tech-stack file: %s", tmp_path)


def default_data() -> TechStackData:
    """Return a TechStackData with all default/empty values.

    Returns:
        A TechStackData object with default values.
    """
    return TechStackData()


def _extract_section(markdown_body: str, section_title: str) -> str:
    """Extract text between '## {section_title}' and the next '## ' heading or end of string.

    Args:
        markdown_body: The full markdown text.
        section_title: The title of the section to extract (case-insensitive).

    Returns:
        The extracted section text, or empty string if not found.
    """
    lines = markdown_body.split("\n")
    section_lines = []
    in_section = False
    target_heading = f"## {section_title}".lower()

    for line in lines:
        if line.lower().startswith("## "):
            if in_section:
                # We've reached the next section, stop
                break
            if line.lower() == target_heading:
                in_section = True
                continue
        elif in_section:
            section_lines.append(line)

    # Return collected lines joined with newlines, stripped
    return "\n".join(section_lines).strip()


def _parse_bullet_list(section_text: str) -> list[str]:
    """Extract bullet items from text. Returns list of strings with '- ' or '* ' prefix stripped.

    Args:
        section_text: The section text containing bullet items.

    Returns:
        A list of bullet item strings without the prefix.
    """
    bullets = []
    lines = section_text.split("\n")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif stripped.startswith("* "):
            bullets.append(stripped[2:].strip())

    return bullets
