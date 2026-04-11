"""Local FastAPI web server for Project Flow.

Serves the bundled frontend and exposes API endpoints that run
scaffold and analyze logic directly against local filesystem paths.
"""

import logging
import platform
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from project_flow.config import get_effective_user_config

logger = logging.getLogger(__name__)

# Path to bundled frontend static files (populated after `npm run build`)
_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Project Flow", docs_url=None, redoc_url=None)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ScaffoldRequest(BaseModel):
    project_name: str
    project_description: str
    output_path: str
    ides: list[str]


class AnalyzeRequest(BaseModel):
    project_path: str
    ides: list[str]
    hint_path: str = ""  # optional extra file to read if no config files auto-detected


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/cwd")
def get_cwd() -> dict:
    """Return the server's current working directory as a default path hint."""
    return {"cwd": str(Path.cwd())}


@app.post("/api/scaffold")
def api_scaffold(req: ScaffoldRequest) -> dict:
    """Run scaffold logic against a local output path."""
    from project_flow.config import load_config
    from project_flow.constants import (
        DEFAULT_CONFIG_FILENAME,
        DEFAULT_PROJECT_DESCRIPTION,
        SUPPORTED_IDES,
        UNKNOWN,
    )
    from project_flow.context import build_generic_context
    from project_flow.models import TechStackData
    from project_flow.scaffolder import generate_planning_stubs
    from project_flow.writer import ArtifactWriter

    # Validate IDEs
    invalid = [i for i in req.ides if i not in SUPPORTED_IDES]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported IDE(s): {invalid}")
    if not req.ides:
        raise HTTPException(status_code=422, detail="At least one IDE must be selected.")

    output_root = Path(req.output_path).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    config_path = output_root / DEFAULT_CONFIG_FILENAME
    if not config_path.exists():
        config_path = Path(DEFAULT_CONFIG_FILENAME)
    config = load_config(config_path)

    project_description = (
        req.project_description
        or (config.project.description if config.project.description != UNKNOWN else "")
        or DEFAULT_PROJECT_DESCRIPTION
    )
    config.project.name = req.project_name
    config.project.description = project_description

    # Override enabled IDEs with request selection
    for ide in SUPPORTED_IDES:
        setattr(config.ides, ide, ide in req.ides)

    tech_stack = TechStackData(
        project_name=req.project_name,
        project_description=project_description,
    )
    context = build_generic_context(config, req.project_name, project_description)

    from project_flow.cli import _collect_artifacts
    artifacts = _collect_artifacts(config, req.ides, tech_stack, context)
    artifacts.extend(generate_planning_stubs(req.project_name, project_description))

    writer = ArtifactWriter(output_root=output_root, backup=False, dry_run=False)
    writer.write_all(artifacts)

    files_written = [
        entry["path"]
        for entry in writer.change_log
        if entry.get("action") in ("CREATE", "UPDATE")
    ]

    return {"files_written": files_written, "output_path": str(output_root)}


@app.post("/api/analyze")
def api_analyze(req: AnalyzeRequest) -> dict:
    """Run AI analyze logic against a local project folder."""
    from project_flow.ai_brain import (
        detect_project_name,
        detect_tech_stack,
        generate_rules,
        generate_skills,
    )
    from project_flow.config import load_config
    from project_flow.constants import (
        DEFAULT_CONFIG_FILENAME,
        DEFAULT_PROJECT_DESCRIPTION,
        SUPPORTED_IDES,
    )
    from project_flow.context import build_ai_context
    from project_flow.models import TechStackData
    from project_flow.scanner import scan_local_project
    from project_flow.tech_stack import parse_from_string
    from project_flow.writer import ArtifactWriter

    invalid = [i for i in req.ides if i not in SUPPORTED_IDES]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported IDE(s): {invalid}")
    if not req.ides:
        raise HTTPException(status_code=422, detail="At least one IDE must be selected.")

    project_root = Path(req.project_path).expanduser().resolve()
    if not project_root.exists():
        raise HTTPException(status_code=422, detail=f"Path not found: {project_root}")

    user_config = get_effective_user_config()
    if not user_config.ai.key or "PLACEHOLDER" in user_config.ai.key:
        raise HTTPException(
            status_code=503,
            detail="AI backend not reachable. Ensure the Render proxy is configured.",
        )

    config_path = project_root / DEFAULT_CONFIG_FILENAME
    if not config_path.exists():
        config_path = Path(DEFAULT_CONFIG_FILENAME)
    config = load_config(config_path)

    for ide in SUPPORTED_IDES:
        setattr(config.ides, ide, ide in req.ides)

    scan_result = scan_local_project(project_root)

    # If no recognizable files found, ask the frontend to provide a hint
    if not scan_result.get("file_contents"):
        if req.hint_path:
            hint = Path(req.hint_path).expanduser().resolve()
            if hint.is_file():
                try:
                    scan_result["file_contents"] = {str(hint): hint.read_text(encoding="utf-8", errors="replace")}
                except OSError:
                    pass
        if not scan_result.get("file_contents"):
            return {"needs_hint": True}

    try:
        ai_tech_stack = detect_tech_stack(scan_result["file_contents"], user_config)
        ai_project_name, ai_project_desc = detect_project_name(scan_result["file_contents"], user_config)
    except (ConnectionError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    from project_flow.cli import _find_tech_stack_content
    tech_stack_content = _find_tech_stack_content(scan_result, config.project.tech_stack_file)
    parsed_stack = parse_from_string(tech_stack_content) if tech_stack_content else TechStackData()

    try:
        ai_rules = generate_rules(ai_tech_stack, user_config, tech_stack_details=parsed_stack.tech_stack_details)
        ai_skills = generate_skills(
            ai_tech_stack, config.skills, user_config,
            repo_url="", tech_stack_details=parsed_stack.tech_stack_details,
        )
    except (ConnectionError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    project_name = ai_project_name or parsed_stack.project_name or config.project.name or project_root.name
    project_desc = ai_project_desc or parsed_stack.project_description or config.project.description or DEFAULT_PROJECT_DESCRIPTION

    config.project.name = project_name
    config.project.description = project_desc

    context = build_ai_context(
        config, project_name, project_desc, ai_tech_stack,
        global_coding_rules=parsed_stack.global_coding_rules,
        tech_stack_details=parsed_stack.tech_stack_details,
    )
    if ai_rules:
        context["AI_GENERATED_RULES"] = ai_rules
    if ai_skills:
        context["AI_GENERATED_SKILLS"] = ai_skills

    tech_stack = TechStackData(
        project_name=project_name,
        project_description=project_desc,
        primary_language=ai_tech_stack.primary_language or parsed_stack.primary_language,
        framework=ai_tech_stack.framework or parsed_stack.framework,
        database=ai_tech_stack.database or parsed_stack.database,
        package_manager=ai_tech_stack.package_manager or parsed_stack.package_manager,
        test_framework=ai_tech_stack.test_framework or parsed_stack.test_framework,
        linting=ai_tech_stack.linting or parsed_stack.linting,
        formatting=ai_tech_stack.formatting or parsed_stack.formatting,
        typing=ai_tech_stack.typing or parsed_stack.typing,
        global_coding_rules=parsed_stack.global_coding_rules,
        tech_stack_details=parsed_stack.tech_stack_details,
    )

    from project_flow.cli import _collect_artifacts
    artifacts = _collect_artifacts(config, req.ides, tech_stack, context)

    writer = ArtifactWriter(output_root=project_root, backup=False, dry_run=False)
    writer.write_all(artifacts)

    files_written = [
        entry["path"]
        for entry in writer.change_log
        if entry.get("action") in ("CREATE", "UPDATE")
    ]

    return {"files_written": files_written, "output_path": str(project_root)}


@app.get("/api/open-folder")
def open_folder(path: str) -> dict:
    """Open a folder in the OS file explorer."""
    folder = Path(path).expanduser().resolve()
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {folder}")

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(folder)])
        elif system == "Windows":
            subprocess.Popen(["explorer", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not open folder: {e}")

    return {"ok": True}


# ---------------------------------------------------------------------------
# Frontend static files (served last so API routes take precedence)
# ---------------------------------------------------------------------------

def _warm_up_render() -> None:
    """Ping the Render proxy in the background so it's warm for first analyze."""
    def _ping() -> None:
        try:
            import requests as _req
            cfg = get_effective_user_config()
            if cfg.ai.endpoint and cfg.ai.key:
                _req.post(
                    cfg.ai.endpoint,
                    json={"model": cfg.ai.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                    headers={"Authorization": f"Bearer {cfg.ai.key}", "Content-Type": "application/json"},
                    timeout=90,
                )
        except Exception:
            pass

    threading.Thread(target=_ping, daemon=True).start()


_warm_up_render()

if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    def frontend_placeholder() -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "message": "Project Flow API is running. "
                           "Frontend not yet bundled — drop built frontend into "
                           "src/project_flow/web/static/ and restart.",
                "api_docs": "/api/cwd",
            },
        )
