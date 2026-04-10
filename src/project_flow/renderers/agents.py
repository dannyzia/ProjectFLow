"""Render agent files from agent configuration."""

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from project_flow import __version__
from project_flow.constants import (
    DEFAULT_KILO_MODE,
    DEFAULT_KILO_PERMISSIONS,
    DEFAULT_LANGUAGE_GLOB,
    DEFAULT_PRIMARY_AGENT,
    TOOL_PERMISSION_MAP,
)
from project_flow.models import AgentConfig

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)), keep_trailing_newline=True
)


def render_agent_file(
    agent: AgentConfig,
    model_id: str,
    frontmatter_fields: list[str],
    context: dict,
    ide: str,
) -> str:
    """Render a complete .agent.md file for one agent. Returns the file content as a string.

    Args:
        agent: The agent configuration.
        model_id: The model ID for this agent in the target IDE.
        frontmatter_fields: List of frontmatter fields to include.
        context: Template context dictionary.
        ide: Target IDE name (affects some field values).

    Returns:
        The rendered file content as a string.
    """
    # Step 1 & 2: Build frontmatter dict from the agent based on frontmatter_fields
    frontmatter_dict = {}

    for field in frontmatter_fields:
        if field == "name":
            frontmatter_dict["name"] = agent.display_name
        elif field == "description":
            frontmatter_dict["description"] = agent.description
        elif field == "tools":
            frontmatter_dict["tools"] = agent.tools
        elif field == "handoffs" and agent.handoffs:
            slug_to_name = {
                a["slug"]: a["display_name"]
                for a in context.get("AVAILABLE_AGENTS", [])
            }
            handoff_list = []
            for h in agent.handoffs:
                ho = {
                    "label": h.label,
                    "agent": slug_to_name.get(h.agent_slug, h.agent_slug),
                    "send": h.send_immediately,
                }
                if h.prompt:
                    ho["prompt"] = h.prompt
                if h.model:
                    ho["model"] = h.model
                handoff_list.append(ho)
            frontmatter_dict["handoffs"] = handoff_list
        elif field == "agents" and agent.allowed_agents:
            slug_to_name = {
                a["slug"]: a["display_name"]
                for a in context.get("AVAILABLE_AGENTS", [])
            }
            frontmatter_dict["agents"] = [
                slug_to_name.get(s, s) for s in agent.allowed_agents
            ]
        elif field == "mode":
            if agent.kilo.mode:
                frontmatter_dict["mode"] = agent.kilo.mode
            else:
                # Determine mode from config-driven primary agent slug
                primary_agent = context.get("KILO_PRIMARY_AGENT", DEFAULT_PRIMARY_AGENT)
                default_mode = context.get("KILO_DEFAULT_MODE", DEFAULT_KILO_MODE)
                frontmatter_dict["mode"] = (
                    "primary" if agent.slug == primary_agent else default_mode
                )
        elif field == "permission":
            frontmatter_dict["permission"] = _compute_kilo_permission(agent.tools)
        elif field == "color":
            frontmatter_dict["color"] = agent.kilo.color
        elif field == "model":
            frontmatter_dict["model"] = model_id
        elif field == "globs":
            frontmatter_dict["globs"] = context.get(
                "LANGUAGE_GLOB", DEFAULT_LANGUAGE_GLOB
            )
        elif field == "alwaysApply":
            frontmatter_dict["alwaysApply"] = True
        # Skip any field not listed above

    # Step 3: Convert frontmatter dict to YAML if non-empty
    if frontmatter_dict:
        frontmatter_yaml = yaml.safe_dump(
            frontmatter_dict,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).strip()
    else:
        # Step 4: Empty frontmatter
        frontmatter_yaml = ""

    # Step 5: Build agent-specific context by merging agent_params
    agent_specific = dict(context)
    agent_params_all = context.get("AGENT_PARAMS", {})
    if agent.slug in agent_params_all:
        agent_specific.update(agent_params_all[agent.slug])

    # Step 6: Render the agent's prompt_text through Jinja2 with merged context
    rendered_prompt = _ENV.from_string(agent.prompt_text).render(**agent_specific)

    # Step 7: Load and render the agent.md.j2 template
    template = _ENV.get_template("agent.md.j2")
    rendered = template.render(
        frontmatter_yaml=frontmatter_yaml,
        prompt_text=rendered_prompt,
        version=__version__,
    )

    # Step 8: Return the rendered string
    return rendered


def _compute_kilo_permission(tools: list[str]) -> str:
    parts = list(DEFAULT_KILO_PERMISSIONS)  # Start with default permissions

    for tool in tools:
        if tool in TOOL_PERMISSION_MAP:
            mapped = TOOL_PERMISSION_MAP[tool]
            if mapped not in parts:
                parts.append(mapped)

    return ",".join(parts)
