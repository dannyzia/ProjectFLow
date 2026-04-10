"""Configuration loader for Project Flow."""

import logging
import os
from pathlib import Path

import yaml

from project_flow.models import (
    AgentConfig,
    AgentHandoff,
    AgentKiloConfig,
    AgentModels,
    DetectedTechStack,
    FullConfig,
    IdeConfig,
    IdeFlags,
    KiloIdeConfig,
    ProjectConfig,
    PromptConfig,
    SkillConfig,
    UserAiConfig,
    UserConfig,
    VsCodeIdeConfig,
    VsCodeModeAgents,
    ZedIdeConfig,
)

import json

from project_flow.constants import (
    DEFAULT_ENCODING,
    DEFAULT_KILO_COLOR,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_PLAN_ARCH_FILE,
    DEFAULT_PLAN_DIR,
    DEFAULT_PLAN_PRD_FILE,
    DEFAULT_PLAN_TECH_STACK_FILE,
    REQUIRED_CONFIG_KEYS,
    SUPPORTED_CONFIG_VERSIONS,
    UNKNOWN,
)

logger = logging.getLogger(__name__)


def _load_default_language_globs() -> dict[str, str]:
    """Load the default language-to-glob mapping from data/language-globs.json."""
    data_file = Path(__file__).parent / "data" / "language-globs.json"
    try:
        with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _resolve_model_alias(model_alias: str) -> dict[str, str]:
    """Look up a model alias in models-registry.json. Returns ids dict (empty on miss)."""
    data_file = Path(__file__).parent / "data" / "models-registry.json"
    try:
        with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
            registry = json.load(f)
        entry = registry.get("models", {}).get(model_alias)
        if entry:
            ids = dict(entry.get("ids", {}))
            ids["vscode_model"] = entry.get("vscode_model", "")
            return ids
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def load_builtin_skills() -> list[SkillConfig]:
    """Load generic skills from data/skills/*.yml.

    File presence = registration — no hardcoding required.
    """
    skills_dir = Path(__file__).parent / "data" / "skills"
    skills = []
    for skill_file in sorted(skills_dir.glob("*.yml")):
        try:
            with open(skill_file, "r", encoding=DEFAULT_ENCODING) as f:
                data = yaml.safe_load(f)
            if not data or "name" not in data:
                continue
            skills.append(
                SkillConfig(
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    content=data.get("content", ""),
                    source_url=data.get("source_url", ""),
                )
            )
        except Exception:
            logger.warning("Failed to load builtin skill: %s", skill_file.name)
    return skills


def load_config(config_path: Path) -> FullConfig:
    """Load project-flow.yml and return a FullConfig object with all agent prompts loaded.

    Args:
        config_path: Path to the project-flow.yml file.

    Returns:
        A FullConfig object with all configuration and agent prompts loaded.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config is empty, invalid, or has an unsupported version.
    """
    # Step 1: Load and parse the YAML file
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding=DEFAULT_ENCODING) as f:
        raw_data = yaml.safe_load(f)

    if raw_data is None:
        raise ValueError(f"Config file is empty or invalid: {config_path}")

    # Step 2: Validate the config version
    config_version = str(raw_data.get("version", ""))

    if config_version == "":
        raise ValueError(
            f'Config file {config_path} is missing the required "version" key. '
            'Add "version: \\"1.0\\"" at the top of the file.'
        )

    if config_version not in SUPPORTED_CONFIG_VERSIONS:
        raise ValueError(
            f"Unsupported config version: {config_version}. "
            f"Supported versions: {SUPPORTED_CONFIG_VERSIONS}. "
            "You may need a newer version of project-flow."
        )

    logger.debug(f"Config version: {config_version}")

    # Step 3: Validate required top-level keys
    required_keys = REQUIRED_CONFIG_KEYS
    missing = required_keys - set(raw_data.keys())

    if missing:
        raise ValueError(f"Config file missing required sections: {sorted(missing)}")

    # Step 4: Extract and parse the 'project' section (optional)
    project_data = raw_data.get("project", {})
    default_plan_root = Path(DEFAULT_PLAN_DIR)
    default_planning_docs = [
        str(default_plan_root / DEFAULT_PLAN_PRD_FILE),
        str(default_plan_root / DEFAULT_PLAN_ARCH_FILE),
        str(default_plan_root / DEFAULT_PLAN_TECH_STACK_FILE),
    ]
    project_config = ProjectConfig(
        name=project_data.get("name", UNKNOWN),
        description=project_data.get("description", UNKNOWN),
        tech_stack_file=project_data.get(
            "tech_stack_file", str(default_plan_root / DEFAULT_PLAN_TECH_STACK_FILE)
        ),
        output_root=project_data.get("output_root", DEFAULT_OUTPUT_ROOT),
        planning_docs=project_data.get("planning_docs", default_planning_docs),
        language_globs=project_data.get(
            "language_globs", _load_default_language_globs()
        ),
    )

    # Step 5: Extract and parse the 'ides' section
    ides_data = raw_data.get("ides", {})
    ide_flags = IdeFlags(
        vscode=ides_data.get("vscode", False),
        kilo=ides_data.get("kilo", False),
        cursor=ides_data.get("cursor", False),
        windsurf=ides_data.get("windsurf", False),
        zed=ides_data.get("zed", False),
        void=ides_data.get("void", False),
        cline=ides_data.get("cline", False),
        claude=ides_data.get("claude", False),
        antigravity=ides_data.get("antigravity", False),
    )

    # Step 6: Extract and parse the 'agents' section
    agents_data = raw_data.get("agents", {})
    agents_list = []

    for slug, agent_data in agents_data.items():
        agent = _parse_agent(slug, agent_data)
        agents_list.append(agent)

    # Step 7: Load prompt text for each agent
    config_dir = config_path.parent

    for agent in agents_list:
        if agent.prompt_file:
            prompt_path = config_dir / agent.prompt_file
            try:
                with open(prompt_path, "r", encoding=DEFAULT_ENCODING) as f:
                    agent.prompt_text = f.read()
            except FileNotFoundError:
                agent.prompt_text = f"PROMPT FILE NOT FOUND: {prompt_path}"
                logger.warning(f"Agent prompt file not found: {prompt_path}")

    # Step 8: Extract and parse the 'prompts' section
    prompts_data = raw_data.get("prompts", [])
    prompts_list = []

    for p in prompts_data:
        prompt = PromptConfig(
            filename=p.get("filename", ""),
            content=p.get("content", ""),
        )
        prompts_list.append(prompt)

    # Step 9: Extract and parse the 'skills' section
    skills_data = raw_data.get("skills", [])
    skills_list = []

    for s in skills_data:
        skill = SkillConfig(
            name=s.get("name", ""),
            description=s.get("description", ""),
            content=s.get("content", ""),
            source_url=s.get("source_url", ""),
        )
        skills_list.append(skill)

    # Step 9b: Merge builtin generic skills (file-based, no hardcoding)
    if raw_data.get("generic_skills", True):
        project_skill_names = {s.name for s in skills_list}
        for builtin in load_builtin_skills():
            if builtin.name not in project_skill_names:
                skills_list.append(builtin)

    # Step 10: Extract and parse the 'ide_config' section (optional)
    ide_config_data = raw_data.get("ide_config", {})

    vscode_config_data = ide_config_data.get("vscode", {})
    mode_agents_data = vscode_config_data.get("mode_agents", {})
    vscode_config = VsCodeIdeConfig(
        mode_agents=VsCodeModeAgents(
            ask=mode_agents_data.get("ask", VsCodeModeAgents().ask),
            edit=mode_agents_data.get("edit", VsCodeModeAgents().edit),
            agent=mode_agents_data.get("agent", VsCodeModeAgents().agent),
        )
    )

    kilo_config_data = ide_config_data.get("kilo", {})
    kilo_ide_config = KiloIdeConfig(
        default_color=kilo_config_data.get(
            "default_color", KiloIdeConfig().default_color
        ),
        default_mode=kilo_config_data.get("default_mode", KiloIdeConfig().default_mode),
        primary_agent=kilo_config_data.get(
            "primary_agent", KiloIdeConfig().primary_agent
        ),
    )

    zed_config_data = ide_config_data.get("zed", {})
    zed_config = ZedIdeConfig(
        provider=zed_config_data.get("provider", ZedIdeConfig().provider),
        assistant_version=zed_config_data.get(
            "assistant_version", ZedIdeConfig().assistant_version
        ),
        primary_agent=zed_config_data.get(
            "primary_agent", ZedIdeConfig().primary_agent
        ),
    )

    ide_config = IdeConfig(
        vscode=vscode_config,
        kilo=kilo_ide_config,
        zed=zed_config,
    )

    # Step 11: Extract agent_params (optional — template variables for agent prompts)
    agent_params_data = raw_data.get("agent_params", {})
    # Flatten: merge _global params into each agent's params
    global_params = agent_params_data.get("_global", {})
    agent_params = {}
    for key, params in agent_params_data.items():
        if key == "_global":
            continue
        merged = dict(global_params)
        merged.update(params if isinstance(params, dict) else {})
        agent_params[key] = merged

    # Step 12: Create and return the FullConfig
    return FullConfig(
        project=project_config,
        ides=ide_flags,
        agents=agents_list,
        prompts=prompts_list,
        skills=skills_list,
        ide_config=ide_config,
        agent_params=agent_params,
    )


def _parse_agent(slug: str, data: dict) -> AgentConfig:
    """Parse a single agent entry from the YAML into an AgentConfig.

    Args:
        slug: The agent's slug (key in the agents dict).
        data: The agent data dictionary from the YAML.

    Returns:
        An AgentConfig object.
    """
    # Support model alias (single string) or explicit models dict
    model_alias = data.get("model", "")
    models_data = data.get("models", {})

    if model_alias and not models_data:
        # Look up model alias from registry
        alias_ids = _resolve_model_alias(model_alias)
        agent_models = AgentModels(
            primary=str(alias_ids.get("primary", model_alias)),
            kilo_id=str(alias_ids.get("kilo", model_alias)),
            vscode_id=str(alias_ids.get("vscode", model_alias)),
            vscode_model=str(alias_ids.get("vscode_model", "")),
            zed_id=str(alias_ids.get("zed", "")),
        )
    else:
        agent_models = AgentModels(
            primary=models_data.get("primary", ""),
            kilo_id=models_data.get("kilo_id", ""),
            vscode_id=models_data.get("vscode_id", ""),
            zed_id=models_data.get("zed_id", ""),
        )

    # Parse handoffs
    handoffs_data = data.get("handoffs", [])
    handoffs_list = []

    for h in handoffs_data:
        handoff = AgentHandoff(
            label=h.get("label", ""),
            agent_slug=h.get("agent_slug", ""),
            prompt=h.get("prompt", ""),
            model=h.get("model", ""),
            send_immediately=h.get("send_immediately", False),
        )
        handoffs_list.append(handoff)

    # Parse Kilo config
    kilo_data = data.get("kilo", {})
    agent_kilo = AgentKiloConfig(
        color=kilo_data.get("color", DEFAULT_KILO_COLOR),
        mode=kilo_data.get("mode", ""),
    )

    # Parse allowed_agents (slugs of agents this agent can call as subagents)
    allowed_agents = data.get("allowed_agents", [])

    # Create and return the AgentConfig
    return AgentConfig(
        slug=slug,
        display_name=data.get("display_name", ""),
        description=data.get("description", ""),
        prompt_file=data.get("prompt_file", ""),
        readonly=data.get("readonly", False),
        tools=data.get("tools", []),
        models=agent_models,
        handoffs=handoffs_list,
        allowed_agents=allowed_agents,
        kilo=agent_kilo,
    )


def _resolve_agent_display_name(config: FullConfig, slug: str) -> str:
    """Resolve an agent slug to its display name. Returns slug if not found."""
    for agent in config.agents:
        if agent.slug == slug:
            return agent.display_name
    return slug


def get_agent(config: FullConfig, slug: str) -> AgentConfig:
    """Return the AgentConfig matching the given slug.

    Args:
        config: The FullConfig object containing all agents.
        slug: The agent slug to look up.

    Returns:
        The AgentConfig matching the slug.

    Raises:
        KeyError: If no agent with the given slug exists.
    """
    for agent in config.agents:
        if agent.slug == slug:
            return agent

    available = [a.slug for a in config.agents]
    raise KeyError(f"Agent not found: {slug}. Available: {available}")


def get_model_id(config: FullConfig, slug: str, ide: str) -> str:
    """Return the model ID string for the given agent slug and IDE name.

    Args:
        config: The FullConfig object.
        slug: The agent slug.
        ide: The IDE name ('kilo', 'vscode', 'zed', or any other for primary).

    Returns:
        The model ID string for the agent in the specified IDE.
    """
    agent = get_agent(config, slug)

    if ide == "kilo":
        return agent.models.kilo_id
    elif ide == "vscode":
        return agent.models.vscode_id
    elif ide == "zed":
        return agent.models.zed_id or agent.models.primary
    else:
        return agent.models.primary


def get_effective_user_config(config_dir: Path | None = None) -> UserConfig:
    """Get effective AI runtime configuration.

    Configuration is sourced from, in precedence order:
    1) Environment variables: PROJECT_FLOW_AI_KEY / PROJECT_FLOW_AI_ENDPOINT / PROJECT_FLOW_AI_MODEL
    2) data/ai-config.json defaults
    """
    _ = config_dir  # compatibility parameter; no filesystem user config is used

    from project_flow.utils import load_ai_config

    ai_defaults = load_ai_config()
    suggestions = ai_defaults.get("auth_suggestions", {})

    return UserConfig(
        ai=UserAiConfig(
            key=os.getenv("PROJECT_FLOW_AI_KEY", "")
            or ai_defaults.get("default_api_key", ""),
            endpoint=os.getenv("PROJECT_FLOW_AI_ENDPOINT", "")
            or suggestions.get("endpoint", ""),
            model=os.getenv("PROJECT_FLOW_AI_MODEL", "")
            or suggestions.get("model", ""),
        )
    )


def get_vscode_model_name(config: FullConfig, slug: str) -> str:
    """Return the VS Code model picker name for the given agent slug.

    Falls back to vscode_id, then primary if vscode_model is not set.
    """
    agent = get_agent(config, slug)
    if agent.models.vscode_model:
        return agent.models.vscode_model
    if agent.models.vscode_id:
        return agent.models.vscode_id
    return agent.models.primary
