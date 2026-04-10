"""Data models for Project Flow. All structured data uses these dataclasses."""

from dataclasses import dataclass, field
from typing import Literal

from project_flow.constants import (
    UNKNOWN,
    DEFAULT_KILO_COLOR,
    DEFAULT_KILO_MODE,
    DEFAULT_PRIMARY_AGENT,
    SUPPORTED_IDES,
)


@dataclass
class AgentModels:
    """Model identifiers for an agent across different IDEs."""

    primary: str = ""
    kilo_id: str = ""
    vscode_id: str = ""
    vscode_model: str = ""  # VS Code model picker name, e.g. "GPT-5.2 (copilot)"
    zed_id: str = ""


@dataclass
class AgentHandoff:
    """Defines a handoff from one agent to another (VS Code spec)."""

    label: str = ""
    agent_slug: str = ""
    prompt: str = ""
    model: str = ""
    send_immediately: bool = False


@dataclass
class AgentKiloConfig:
    """Kilo-specific agent configuration."""

    color: str = DEFAULT_KILO_COLOR
    mode: str = ""


@dataclass
class AgentConfig:
    """Complete configuration for one agent."""

    slug: str = ""
    display_name: str = ""
    description: str = ""
    prompt_file: str = ""
    prompt_text: str = ""
    readonly: bool = False
    tools: list[str] = field(default_factory=list)
    models: AgentModels = field(default_factory=AgentModels)
    handoffs: list[AgentHandoff] = field(default_factory=list)
    allowed_agents: list[str] = field(
        default_factory=list
    )  # Slugs of agents this agent can call as subagents
    kilo: AgentKiloConfig = field(default_factory=AgentKiloConfig)


@dataclass
class PromptConfig:
    """A reusable prompt file definition from config."""

    filename: str = ""
    content: str = ""


@dataclass
class SkillConfig:
    """A skill definition from config."""

    name: str = ""
    description: str = ""
    content: str = ""
    source_url: str = ""


@dataclass
class ProjectConfig:
    """Project-level settings from the 'project' section of project-flow.yml."""

    name: str = UNKNOWN
    description: str = UNKNOWN
    tech_stack_file: str = ""
    output_root: str = "."
    planning_docs: list[str] = field(default_factory=list)
    language_globs: dict[str, str] = field(default_factory=dict)
    generic_skills_enabled: bool = True


@dataclass
class IdeFlags:
    """Which IDEs to generate files for. From the 'ides' section of project-flow.yml."""

    vscode: bool = True
    kilo: bool = False
    cursor: bool = False
    windsurf: bool = False
    zed: bool = False
    void: bool = False
    cline: bool = False
    claude: bool = False
    antigravity: bool = False


@dataclass
class TechStackData:
    """Parsed data from a Tech_Stack.md file."""

    project_name: str = UNKNOWN
    project_description: str = UNKNOWN
    primary_language: str = UNKNOWN
    framework: str = UNKNOWN
    database: str = UNKNOWN
    package_manager: str = UNKNOWN
    test_framework: str = UNKNOWN
    linting: str = UNKNOWN
    formatting: str = UNKNOWN
    typing: str = UNKNOWN
    global_coding_rules: list[str] = field(default_factory=list)
    tech_stack_details: str = ""
    raw_content: str = ""


@dataclass(frozen=True)
class Artifact:
    """A single file to be written to the target project."""

    path: str
    content: str
    mode: Literal["create", "overwrite", "json_merge"] = "create"
    source: str = ""


@dataclass
class VsCodeModeAgents:
    """Maps VS Code chat modes to agent slugs for settings.json generation."""

    ask: str = "ask"
    edit: str = "code"
    agent: str = DEFAULT_PRIMARY_AGENT


@dataclass
class VsCodeIdeConfig:
    """VS Code-specific IDE configuration."""

    mode_agents: VsCodeModeAgents = field(default_factory=VsCodeModeAgents)


@dataclass
class KiloIdeConfig:
    """Kilo-specific IDE configuration defaults."""

    default_color: str = DEFAULT_KILO_COLOR
    default_mode: str = DEFAULT_KILO_MODE
    primary_agent: str = DEFAULT_PRIMARY_AGENT


@dataclass
class ZedIdeConfig:
    """Zed-specific IDE configuration."""

    provider: str = "openrouter"
    assistant_version: str = "2"
    primary_agent: str = DEFAULT_PRIMARY_AGENT


@dataclass
class IdeConfig:
    """IDE-specific configuration loaded from the ide_config section of project-flow.yml."""

    vscode: VsCodeIdeConfig = field(default_factory=VsCodeIdeConfig)
    kilo: KiloIdeConfig = field(default_factory=KiloIdeConfig)
    zed: ZedIdeConfig = field(default_factory=ZedIdeConfig)


@dataclass
class FullConfig:
    """All configuration loaded from project-flow.yml."""

    project: ProjectConfig = field(default_factory=ProjectConfig)
    ides: IdeFlags = field(default_factory=IdeFlags)
    agents: list[AgentConfig] = field(default_factory=list)
    prompts: list[PromptConfig] = field(default_factory=list)
    skills: list[SkillConfig] = field(default_factory=list)
    ide_config: IdeConfig = field(default_factory=IdeConfig)
    agent_params: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class UserAiConfig:
    """AI credentials and settings from runtime configuration sources."""

    key: str = ""
    endpoint: str = ""
    model: str = ""


@dataclass
class UserConfig:
    """Runtime AI configuration container."""

    ai: UserAiConfig = field(default_factory=UserAiConfig)


@dataclass
class DetectedTechStack:
    """Tech stack detected by AI brain from repo scan."""

    primary_language: str = ""
    framework: str = ""
    database: str = ""
    package_manager: str = ""
    test_framework: str = ""
    linting: str = ""
    formatting: str = ""
    typing: str = ""
    project_name: str = ""
    project_description: str = ""
    confidence: float = 0.0
