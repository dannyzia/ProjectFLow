"""Cursor IDE generator.

Generates:
  - .cursorrules: Main Cursor rules file
  - .cursor/rules/{agent_slug}.mdc: Per-agent scoped rule files
"""

import logging

from project_flow.models import Artifact, FullConfig, TechStackData
from project_flow.renderers.agents import render_agent_file
from project_flow.renderers.rules import render_instructions
from project_flow.utils import load_ide_paths

logger = logging.getLogger(__name__)


def generate(
    config: FullConfig, tech_stack: TechStackData, context: dict
) -> list[Artifact]:
    """Generate Cursor IDE configuration files.

    Cursor generates a main .cursorrules file and per-agent .mdc scoped rule files.

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of Artifact objects: .cursorrules + per-agent .mdc files + skills
    """
    ide_paths = load_ide_paths("cursor")
    artifacts = []

    if config.prompts:
        logger.warning(
            "Cursor does not support prompts. %d prompt(s) skipped.",
            len(config.prompts),
        )

    # Generate main rules file
    instructions_content = render_instructions(tech_stack, context)

    artifacts.append(
        Artifact(
            path=ide_paths["rules_file"],
            content=instructions_content,
            source="cursor",
        )
    )

    # Generate per-agent scoped rule files using shared renderer
    frontmatter_fields = ide_paths.get(
        "frontmatter_fields", ["name", "description", "globs", "alwaysApply"]
    )

    for agent in config.agents:
        content = render_agent_file(agent, "", frontmatter_fields, context, "cursor")

        path = ide_paths["agent_file"].format(slug=agent.slug)

        artifacts.append(Artifact(path=path, content=content, source="cursor"))

    # Generate skill files for Cursor
    if config.skills:
        from project_flow.renderers.skills import render_skill_file, render_skills

        skills = render_skills(config.skills, context)
        for skill in skills:
            content = render_skill_file(skill)
            path = ide_paths["skill_file"].format(skill_name=skill["name"])
            artifacts.append(Artifact(path=path, content=content, source="cursor"))
    else:
        logger.info("No skills configured for Cursor.")

    return artifacts
