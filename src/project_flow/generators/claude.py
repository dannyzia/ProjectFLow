"""Claude Code generator for project-flow.

Generates skill files for Claude Code:
  - .claude/skills/{skill_name}/SKILL.md
"""

import logging

from project_flow.models import Artifact, FullConfig, TechStackData
from project_flow.utils import load_ide_paths
from project_flow.renderers.skills import render_skill_file, render_skills

logger = logging.getLogger(__name__)


def generate(
    config: FullConfig, tech_stack: TechStackData, context: dict
) -> list[Artifact]:
    """Generate Claude Code skill files.

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of Artifact objects: one SKILL.md per configured skill.
    """
    ide_paths = load_ide_paths("claude")
    artifacts = []

    if not config.skills:
        logger.info("No skills configured. Skipping Claude Code skill generation.")
        return artifacts

    # Render and generate skill files
    skills = render_skills(config.skills, context)

    for skill in skills:
        content = render_skill_file(skill)
        path = ide_paths["skill_file"].format(skill_name=skill["name"])
        artifacts.append(Artifact(path=path, content=content, source="claude"))

    return artifacts
