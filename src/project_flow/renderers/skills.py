"""Render skill files from skill configuration."""

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from project_flow import __version__
from project_flow.models import SkillConfig

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)), keep_trailing_newline=True
)


def render_skills(skills: list[SkillConfig], context: dict) -> list[dict]:
    """Render skill definitions from config. Returns list of dicts with keys: name, description, rendered_content.

    Args:
        skills: List of SkillConfig objects from project-flow.yml.
        context: Template context dictionary (includes PROJECT_NAME, TEST_FRAMEWORK, etc.).

    Returns:
        A list of dicts with keys: name, description, content (rendered).

    NOTE:
        The skill content comes from project-flow.yml's 'skills' section. It uses
        standard Jinja2 {{ VARIABLE }} syntax which is rendered here. No hardcoded
        skill text.
    """
    result = []

    for skill in skills:
        # Step 1a: Render the skill's content string through Jinja2
        rendered_content = _ENV.from_string(skill.content).render(**context)

        # Step 1b: Append to result list
        result.append(
            {
                "name": skill.name,
                "description": skill.description,
                "content": rendered_content,
            }
        )

    # Step 2: Return the result list
    return result


def render_skill_file(skill: dict) -> str:
    """Render a SKILL.md file from a skill dict.

    Args:
        skill: A dict with keys: name, description, content (already rendered).

    Returns:
        The rendered skill file content as a string.
    """
    # Step 1: Build frontmatter dict
    frontmatter_dict = {
        "name": skill["name"],
        "description": skill["description"],
    }

    # Step 2: Convert to YAML
    frontmatter_yaml = yaml.safe_dump(
        frontmatter_dict,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()

    # Step 3: Load skill.md.j2 template and render
    template = _ENV.get_template("skill.md.j2")
    rendered = template.render(
        frontmatter_yaml=frontmatter_yaml,
        skill_content=skill["content"],
        version=__version__,
    )

    # Step 4: Return the rendered string
    return rendered
