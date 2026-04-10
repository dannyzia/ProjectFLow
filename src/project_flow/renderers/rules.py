"""Render instructions file from tech stack data."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from project_flow import __version__
from project_flow.models import TechStackData

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)), keep_trailing_newline=True
)


def render_instructions(tech_stack: TechStackData, context: dict) -> str:
    """Render the main AI instructions file content.

    Args:
        tech_stack: The parsed tech stack data.
        context: Template context dictionary (must include PLANNING_DOCS).

    Returns:
        The rendered instructions file content as a string.

    NOTE:
        The template uses PLANNING_DOCS (a list from config) for the Planning
        Documents section instead of hardcoded paths. The context must include
        PLANNING_DOCS from build_context().
    """
    # Step 1: Load the comprehensive rules
    comprehensive_rules_path = (
        Path(__file__).parent.parent / "data" / "comprehensive-rules.md"
    )
    with open(comprehensive_rules_path, "r", encoding="utf-8") as f:
        comprehensive_rules = f.read().strip()

    # Step 2: Load the instructions.md.j2 template
    template = _ENV.get_template("instructions.md.j2")

    # Step 3: Render with all context dict items unpacked, plus version
    rendered = template.render(**context, version=__version__)

    # Step 4: Prepend comprehensive rules and return
    return comprehensive_rules + "\n\n" + rendered
