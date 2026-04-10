"""Zed IDE generator.

Generates two artifacts:
  - .zed/settings.json: Zed configuration with assistant model defaults
  - .zed/prompts/project-context.md: Project context and instructions
"""

import json
import logging

from project_flow.config import get_model_id
from project_flow.constants import (
    JSON_INDENT,
    JSON_MERGE_MODE,
    UNKNOWN,
)
from project_flow.utils import load_ide_paths
from project_flow.models import Artifact, FullConfig, TechStackData
from project_flow.renderers.rules import render_instructions

logger = logging.getLogger(__name__)


def generate(
    config: FullConfig, tech_stack: TechStackData, context: dict
) -> list[Artifact]:
    """Generate Zed IDE configuration files.

    Zed generates settings.json (json_merge mode) and project context file.
    The settings.json includes the default model from config.

    Args:
        config: The full configuration object.
        tech_stack: Parsed tech stack data.
        context: Template context dictionary.

    Returns:
        List of 2 Artifact objects: .zed/settings.json and .zed/prompts/project-context.md
    """
    ide_paths = load_ide_paths("zed")
    artifacts = []

    if config.skills:
        logger.warning(
            "Zed does not support skills. %d skill(s) skipped.", len(config.skills)
        )
    if config.prompts:
        logger.warning(
            "Zed does not support prompts. %d prompt(s) skipped.", len(config.prompts)
        )

    # Get the primary model ID for Zed from config-driven primary agent
    zed_config = config.ide_config.zed
    model_id = get_model_id(config, zed_config.primary_agent, "zed") or ""

    # Build settings.json merge data using config-driven values
    settings_data = {
        "assistant": {
            "version": zed_config.assistant_version,
            "default_model": {
                "provider": zed_config.provider,
                "model": model_id if model_id else UNKNOWN,
            },
        }
    }

    # Artifact 1: .zed/settings.json (json_merge mode)
    artifacts.append(
        Artifact(
            path=ide_paths["settings"],
            content=json.dumps(settings_data, indent=JSON_INDENT),
            mode=JSON_MERGE_MODE,
            source="zed",
        )
    )

    # Artifact 2: .zed/prompts/project-context.md
    instructions_content = render_instructions(tech_stack, context)

    artifacts.append(
        Artifact(
            path=ide_paths["context_file"],
            content=instructions_content,
            source="zed",
        )
    )

    # Generate .rules file for Zed (auto-detected at project root)
    rules_content = render_instructions(tech_stack, context)
    artifacts.append(
        Artifact(
            path=ide_paths["rules_file"],
            content=rules_content,
            source="zed",
        )
    )

    return artifacts
