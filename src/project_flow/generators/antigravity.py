"""Antigravity / Open Standard generator for project-flow.

Generates:
  - .agents/rules/{slug}.md: Per-agent rule files
  - .agents/skills/{skill_name}/SKILL.md: Skill files
"""

import logging

from project_flow.models import Artifact, FullConfig, TechStackData
from project_flow.renderers.agents import render_agent_file
from project_flow.renderers.rules import render_instructions
from project_flow.renderers.skills import render_skill_file, render_skills
from project_flow.utils import load_ide_paths

logger = logging.getLogger(__name__)


def generate(
    config: FullConfig, tech_stack: TechStackData, context: dict
) -> list[Artifact]:
    """Generate Antigravity agent rules and skill files.

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of Artifact objects: per-agent rules + skill files.
    """
    ide_paths = load_ide_paths("antigravity")
    artifacts = []

    # Generate per-agent rule files using shared renderer
    instructions_content = render_instructions(tech_stack, context)
    frontmatter_fields = ide_paths.get("frontmatter_fields", ["name", "description"])

    for agent in config.agents:
        content = render_agent_file(
            agent, "", frontmatter_fields, context, "antigravity"
        )
        path = ide_paths["rule_file"].format(slug=agent.slug)
        artifacts.append(Artifact(path=path, content=content, source="antigravity"))

    # Generate skill files
    if config.skills:
        skills = render_skills(config.skills, context)

        for skill in skills:
            content = render_skill_file(skill)
            path = ide_paths["skill_file"].format(skill_name=skill["name"])
            artifacts.append(Artifact(path=path, content=content, source="antigravity"))

    return artifacts
