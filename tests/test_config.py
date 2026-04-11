"""Tests for config loading."""

from pathlib import Path

from project_flow.config import get_agent, get_model_id, load_config
from project_flow.constants import UNKNOWN
from project_flow.context import build_context
from project_flow.models import FullConfig, TechStackData
from project_flow.tech_stack import default_data, parse


def test_load_config_returns_11_agents(config_path: Path) -> None:
    """Config must load exactly 11 agents."""
    config = load_config(config_path)
    assert len(config.agents) == 11


def test_all_agents_have_prompt_text(config_path: Path) -> None:
    """Every agent must have non-empty prompt_text after loading."""
    config = load_config(config_path)
    for agent in config.agents:
        assert len(agent.prompt_text) > 10, f"Agent {agent.slug} has empty prompt_text"


def test_get_agent_finds_orchestrator(config_path: Path) -> None:
    """get_agent must find the orchestrator by slug."""
    config = load_config(config_path)
    agent = get_agent(config, "orchestrator")
    assert agent is not None
    assert agent.display_name == "Orchestrator"
    assert agent.kilo.color == "red"
    assert len(agent.allowed_agents) > 0


def test_get_agent_returns_none_for_missing_slug() -> None:
    """get_agent must return None (not raise) when slug is absent."""
    from project_flow.models import FullConfig

    config = FullConfig()
    assert get_agent(config, "nonexistent") is None


def test_get_model_id_kilo(config_path: Path) -> None:
    """get_model_id for kilo must return the kilo_id."""
    config = load_config(config_path)
    model = get_model_id(config, "orchestrator", "kilo")
    assert model == "moonshot/kimi-k2.5"


def test_readonly_agents_have_no_edit_tool(config_path: Path) -> None:
    """Readonly agents must not have edit or run/terminal tools."""
    config = load_config(config_path)
    for agent in config.agents:
        if agent.readonly:
            assert "edit" not in agent.tools, (
                f"{agent.slug} is readonly but has edit tool"
            )
            assert "run/terminal" not in agent.tools, (
                f"{agent.slug} is readonly but has run/terminal tool"
            )


def test_default_tech_stack() -> None:
    """default_data must return all UNKNOWN values."""
    d = default_data()
    assert d.project_name == UNKNOWN
    assert d.global_coding_rules == []


def test_build_context_summary() -> None:
    """build_context must produce a comma-separated tech stack summary."""
    config = FullConfig()
    ts = TechStackData(primary_language="Python", framework="FastAPI")
    ctx = build_context(config, ts)
    assert ctx["TECH_STACK_SUMMARY"] == "Python, FastAPI"
