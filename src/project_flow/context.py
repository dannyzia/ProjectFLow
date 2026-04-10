"""Build the Jinja2 template context from config and tech stack data."""

from project_flow.constants import UNKNOWN, DEFAULT_LANGUAGE_GLOB
from project_flow.models import DetectedTechStack, FullConfig, TechStackData


def _build_context_from_tech_stack(config: FullConfig, tech_stack: TechStackData) -> dict:
    """Return a dict of template variables built from config and normalized tech-stack data."""
    tech_summary_parts = []
    if tech_stack.primary_language != UNKNOWN:
        tech_summary_parts.append(tech_stack.primary_language)
    if tech_stack.framework != UNKNOWN:
        tech_summary_parts.append(tech_stack.framework)
    if tech_stack.database != UNKNOWN:
        tech_summary_parts.append(tech_stack.database)

    language_glob = config.project.language_globs.get(
        tech_stack.primary_language, DEFAULT_LANGUAGE_GLOB
    )

    available_agents = [
        {"slug": a.slug, "display_name": a.display_name, "description": a.description}
        for a in config.agents
    ]

    return {
        "PROJECT_NAME": config.project.name,
        "PROJECT_DESCRIPTION": config.project.description,
        "PRIMARY_LANGUAGE": tech_stack.primary_language,
        "FRAMEWORK": tech_stack.framework,
        "DATABASE": tech_stack.database,
        "PACKAGE_MANAGER": tech_stack.package_manager,
        "TEST_FRAMEWORK": tech_stack.test_framework,
        "LINTING": tech_stack.linting,
        "FORMATTING": tech_stack.formatting,
        "TYPING": tech_stack.typing,
        "TECH_STACK_SUMMARY": ", ".join(tech_summary_parts)
        if tech_summary_parts
        else UNKNOWN,
        "GLOBAL_CODING_RULES": tech_stack.global_coding_rules,
        "TECH_STACK_DETAILS": tech_stack.tech_stack_details,
        "PLANNING_DOCS": config.project.planning_docs,
        "LANGUAGE_GLOB": language_glob,
        "KILO_PRIMARY_AGENT": config.ide_config.kilo.primary_agent,
        "KILO_DEFAULT_MODE": config.ide_config.kilo.default_mode,
        "KILO_DEFAULT_COLOR": config.ide_config.kilo.default_color,
        "AVAILABLE_AGENTS": available_agents,
        "AGENT_PARAMS": config.agent_params,
    }


def build_generic_context(config: FullConfig, project_name: str, project_description: str = UNKNOWN) -> dict:
    """Build context for scaffold stage with unknown tech stack and known project identity."""
    tech_stack = TechStackData(
        project_name=project_name,
        project_description=project_description,
    )
    context = _build_context_from_tech_stack(config, tech_stack)
    context["PROJECT_NAME"] = project_name
    context["PROJECT_DESCRIPTION"] = project_description
    return context


def build_ai_context(
    config: FullConfig,
    project_name: str,
    project_description: str,
    detected: DetectedTechStack,
    global_coding_rules: list[str] | None = None,
    tech_stack_details: str = "",
) -> dict:
    """Build context for analyze stage from AI-detected stack data."""
    tech_stack = TechStackData(
        project_name=project_name or UNKNOWN,
        project_description=project_description or UNKNOWN,
        primary_language=detected.primary_language or UNKNOWN,
        framework=detected.framework or UNKNOWN,
        database=detected.database or UNKNOWN,
        package_manager=detected.package_manager or UNKNOWN,
        test_framework=detected.test_framework or UNKNOWN,
        linting=detected.linting or UNKNOWN,
        formatting=detected.formatting or UNKNOWN,
        typing=detected.typing or UNKNOWN,
        global_coding_rules=global_coding_rules or [],
        tech_stack_details=tech_stack_details,
    )
    context = _build_context_from_tech_stack(config, tech_stack)
    context["PROJECT_NAME"] = project_name or UNKNOWN
    context["PROJECT_DESCRIPTION"] = project_description or UNKNOWN
    return context


def build_context(config: FullConfig, tech_stack: TechStackData) -> dict:
    """Backward-compatible context builder for legacy call sites."""
    return _build_context_from_tech_stack(config, tech_stack)
