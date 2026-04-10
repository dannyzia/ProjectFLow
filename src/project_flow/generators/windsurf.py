"""Windsurf generator for project-flow."""

import logging

from project_flow.models import Artifact, FullConfig, TechStackData
from project_flow.utils import load_ide_paths
from project_flow.renderers.rules import render_instructions

logger = logging.getLogger(__name__)


def generate(
    config: FullConfig, tech_stack: TechStackData, context: dict
) -> list[Artifact]:
    """Generate Windsurf configuration files.

    Generates 2 artifacts:
    - .windsurfrules: Plain markdown rules file
    - .windsurf/rules/coding-standards.md: Duplicate of rules in subdirectory

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of 2 Artifact objects for Windsurf configuration.
    """
    ide_paths = load_ide_paths("windsurf")
    artifacts = []

    if config.prompts:
        logger.warning(
            "Windsurf does not support prompts. %d prompt(s) skipped.",
            len(config.prompts),
        )

    # Generate instructions content (plain markdown, no frontmatter)
    instructions_content = render_instructions(tech_stack, context)

    # Artifact 1: .windsurfrules
    artifacts.append(
        Artifact(
            path=ide_paths["rules_file"],
            content=instructions_content,
            source="windsurf",
        )
    )

    # Artifact 2: .windsurf/rules/coding-standards.md
    artifacts.append(
        Artifact(
            path=ide_paths["coding_standards"],
            content=instructions_content,
            source="windsurf",
        )
    )

    # Generate workflow files for Windsurf (from skills)
    if config.skills:
        from project_flow.renderers.skills import render_skills

        _WORKFLOW_TEMPLATE = (
            "# Title: {name}\n# Description: {description}\n\n{content}"
        )

        skills = render_skills(config.skills, context)
        for skill in skills:
            workflow_content = _WORKFLOW_TEMPLATE.format(
                name=skill["name"],
                description=skill["description"],
                content=skill["content"],
            )
            path = ide_paths["workflow_file"].format(skill_name=skill["name"])
            artifacts.append(
                Artifact(path=path, content=workflow_content, source="windsurf")
            )
    else:
        logger.info("No skills configured for Windsurf workflows.")

    return artifacts
