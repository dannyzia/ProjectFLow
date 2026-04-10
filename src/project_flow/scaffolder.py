"""Planning document scaffold generation."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from project_flow.constants import (
    DEFAULT_PLAN_ADR_FILE,
    DEFAULT_PLAN_API_FILE,
    DEFAULT_PLAN_ARCH_FILE,
    DEFAULT_PLAN_CONVENTIONS_FILE,
    DEFAULT_PLAN_DATA_MODEL_FILE,
    DEFAULT_PLAN_DEV_CHECKLIST_FILE,
    DEFAULT_PLAN_DEV_SETUP_FILE,
    DEFAULT_PLAN_DIR,
    DEFAULT_PLAN_ENV_VARS_FILE,
    DEFAULT_PLAN_FOLDER_STRUCTURE_FILE,
    DEFAULT_PLAN_GLOSSARY_FILE,
    DEFAULT_PLAN_INCIDENT_RESPONSE_FILE,
    DEFAULT_PLAN_KNOWN_ISSUES_FILE,
    DEFAULT_PLAN_MONITORING_FILE,
    DEFAULT_PLAN_PRD_FILE,
    DEFAULT_PLAN_RUNBOOK_FILE,
    DEFAULT_PLAN_TECH_STACK_FILE,
    DEFAULT_PLAN_UI_SPEC_FILE,
    DEFAULT_PLAN_USER_FLOWS_FILE,
    DEFAULT_PLAN_UX_SPEC_FILE,
)
from project_flow.models import Artifact

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)), keep_trailing_newline=True
)


def generate_planning_stubs(
    project_name: str,
    project_description: str,
    plan_dir: str = DEFAULT_PLAN_DIR,
) -> list[Artifact]:
    """Generate baseline planning documents for a new project scaffold."""
    plan_root = Path(plan_dir)
    ctx = {"project_name": project_name, "project_description": project_description}

    def _render(template_name: str) -> str:
        return _ENV.get_template(template_name).render(**ctx)

    return [
        Artifact(path=str(plan_root / DEFAULT_PLAN_PRD_FILE), content=_render("prd.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_ARCH_FILE), content=_render("architecture.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_TECH_STACK_FILE), content=_render("tech-stack.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_ADR_FILE), content=_render("adr.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_DATA_MODEL_FILE), content=_render("data-model.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_API_FILE), content=_render("api.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_USER_FLOWS_FILE), content=_render("user-flows.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_UI_SPEC_FILE), content=_render("ui-spec.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_UX_SPEC_FILE), content=_render("ux-spec.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_DEV_SETUP_FILE), content=_render("dev-setup.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_ENV_VARS_FILE), content=_render("env-vars.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_FOLDER_STRUCTURE_FILE), content=_render("folder-structure.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_CONVENTIONS_FILE), content=_render("conventions.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_DEV_CHECKLIST_FILE), content=_render("dev-checklist.json.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_RUNBOOK_FILE), content=_render("runbook-deploy.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_INCIDENT_RESPONSE_FILE), content=_render("incident-response.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_MONITORING_FILE), content=_render("monitoring.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_KNOWN_ISSUES_FILE), content=_render("known-issues.md.j2"), source="scaffold"),
        Artifact(path=str(plan_root / DEFAULT_PLAN_GLOSSARY_FILE), content=_render("glossary.md.j2"), source="scaffold"),
    ]

