"""Void IDE generator.

Generates:
  - .void/rules.md: Project instructions/rules
  - .void/agents/{agent_slug}.md: Per-agent rule files with frontmatter
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
    """Generate Void configuration files.

    Void generates a main rules file plus one agent-specific rule file per agent.
    Each agent file includes frontmatter with: name, description, tools.

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of Artifact objects: 1 main rules file + per-agent rule files.
    """
    ide_paths = load_ide_paths("void")
    artifacts = []

    if config.skills:
        logger.warning(
            "Void does not support skills. %d skill(s) skipped.", len(config.skills)
        )
    if config.prompts:
        logger.warning(
            "Void does not support prompts. %d prompt(s) skipped.", len(config.prompts)
        )

    # Main project rules file
    instructions_content = render_instructions(tech_stack, context)

    artifacts.append(
        Artifact(
            path=ide_paths["rules_file"],
            content=instructions_content,
            source="void",
        )
    )

    # Generate agent-specific rule files using shared renderer
    frontmatter_fields = ide_paths.get(
        "frontmatter_fields", ["name", "description", "tools"]
    )

    for agent in config.agents:
        content = render_agent_file(agent, "", frontmatter_fields, context, "void")

        path = ide_paths["agent_file"].format(slug=agent.slug)

        artifacts.append(Artifact(path=path, content=content, source="void"))

    return artifacts
