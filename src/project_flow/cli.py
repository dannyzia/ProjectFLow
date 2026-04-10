"""CLI entry point for Project Flow."""

import argparse
import logging
import sys
from pathlib import Path

from project_flow.constants import (
    CLI_PROG_NAME,
    DEFAULT_PLAN_TECH_STACK_FILE,
    DEFAULT_PROJECT_DESCRIPTION,
    DEFAULT_CONFIG_FILENAME,
    LOG_FORMAT_DEFAULT,
    LOG_FORMAT_QUIET,
    LOG_FORMAT_VERBOSE,
    SUPPORTED_IDES,
    UNKNOWN,
    __version__,
)
from project_flow.config import load_config
from project_flow.context import build_ai_context, build_generic_context
from project_flow.models import Artifact
from project_flow.scaffolder import generate_planning_stubs
from project_flow.scanner import parse_repo_url, scan_local_project
from project_flow.tech_stack import parse_from_string
from project_flow.writer import ArtifactWriter

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the project-flow CLI."""
    # Step 1: Create parent parser with shared arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_FILENAME,
        help="Path to project-flow.yml config file.",
    )
    parent_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose/debug output.",
    )
    parent_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors.",
    )

    # Step 2: Create main ArgumentParser
    parser = argparse.ArgumentParser(
        prog=CLI_PROG_NAME,
        description="Generate AI-assistant configuration files for your project.",
    )

    # Step 3: Add --version flag
    parser.add_argument(
        "--version",
        action="version",
        version=f"{CLI_PROG_NAME} {__version__}",
    )

    # Step 4: Create subparsers with parent parser
    subparsers = parser.add_subparsers(dest="command")

    # Step 5: Subcommand 'scaffold'
    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Generate generic project scaffold artifacts.",
        parents=[parent_parser],
    )
    scaffold_parser.add_argument(
        "--ides",
        type=str,
        default="",
        help="Comma-separated IDE list (e.g. vscode,cursor). If omitted, uses config-enabled IDEs.",
    )
    scaffold_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate files for all 9 supported IDEs, including those disabled in config.",
    )
    scaffold_parser.add_argument(
        "--project-name",
        type=str,
        default="",
        help="Project name override. If omitted, prompted interactively.",
    )
    scaffold_parser.add_argument(
        "--parent-dir",
        type=str,
        default="",
        help="Parent directory where project folder will be created.",
    )
    scaffold_parser.add_argument(
        "--output-root",
        type=str,
        default="",
        help="Explicit output path. If omitted, uses <parent-dir>/<project-name>.",
    )
    scaffold_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing.",
    )
    scaffold_parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backup files."
    )
    scaffold_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Non-interactive: accept all defaults without prompting.",
    )

    # Step 6: Subcommand 'analyze'
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run AI analysis and generate project-specific artifacts.",
        parents=[parent_parser],
    )
    analyze_parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to the local project folder to analyze.",
    )
    analyze_parser.add_argument(
        "--ides",
        type=str,
        default="",
        help="Comma-separated IDE list (e.g. vscode,cursor). If omitted, uses config-enabled IDEs.",
    )
    analyze_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate files for all 9 supported IDEs, including those disabled in config.",
    )
    analyze_parser.add_argument(
        "--output-root",
        type=str,
        default=".",
        help="Root directory of the target project.",
    )
    analyze_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing.",
    )
    analyze_parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backup files."
    )

    # Step 7: Subcommand 'serve'
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the Project Flow web UI at localhost.",
        parents=[parent_parser],
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080).",
    )
    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically.",
    )

    # Step 8: Parse args. If no command given, print help and exit 1.
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Step 9: Configure logging based on --verbose/--quiet flags
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT_VERBOSE)
    elif args.quiet:
        logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT_QUIET)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT_DEFAULT)

    # Step 10: Wrap the rest in try/except
    try:
        if args.command == "serve":
            _handle_serve(args)
            return

        config = load_config(Path(args.config))

        if args.command == "scaffold":
            _handle_scaffold(args, config)

        if args.command == "analyze":
            _handle_analyze(args, config)

    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"CONFIG ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        sys.exit(1)


def _collect_selected_ides(args: argparse.Namespace, config) -> list[str]:
    """Resolve selected IDE names from command args and config flags."""
    if args.all:
        return list(SUPPORTED_IDES)

    if getattr(args, "ides", ""):
        requested = [i.strip() for i in args.ides.split(",") if i.strip()]
        invalid = [i for i in requested if i not in SUPPORTED_IDES]
        if invalid:
            raise ValueError(
                f"Unsupported IDE(s): {invalid}. Supported: {SUPPORTED_IDES}"
            )
        return requested

    enabled = [ide for ide in SUPPORTED_IDES if getattr(config.ides, ide, False)]
    if not enabled:
        raise ValueError("No enabled IDEs found in configuration.")
    return enabled


def _collect_artifacts(config, selected_ides: list[str], tech_stack, context: dict) -> list[Artifact]:
    """Collect rendered artifacts from all selected generators."""
    from project_flow.generators.registry import get_all_generators

    all_generators = get_all_generators()
    all_artifacts: list[Artifact] = []

    for ide_name in selected_ides:
        gen_func = all_generators[ide_name]
        artifacts = gen_func(config, tech_stack, context)
        all_artifacts.extend(artifacts)
        logger.info("=== %s generation complete (%d files) ===", ide_name, len(artifacts))

    _validate_no_path_conflicts(all_artifacts)
    return all_artifacts


def _validate_no_path_conflicts(artifacts: list[Artifact]) -> None:
    """Raise if multiple generators write different sources to the same path."""
    seen_paths: dict[str, str] = {}
    conflicts: list[str] = []
    for artifact in artifacts:
        if artifact.path in seen_paths:
            conflicts.append(
                f"  {artifact.path} — written by both {seen_paths[artifact.path]} and {artifact.source}"
            )
        else:
            seen_paths[artifact.path] = artifact.source

    if conflicts:
        raise ValueError(
            "Path conflicts detected between generators:\n" + "\n".join(conflicts)
        )


def _resolve_scaffold_output_root(args: argparse.Namespace, default_name: str = "") -> tuple[Path, str]:
    """Resolve scaffold output root and project name from args and interactive input."""
    yes = getattr(args, "yes", False)
    default_project_name = args.project_name or default_name or DEFAULT_PROJECT_NAME
    project_name = args.project_name.strip() if args.project_name else ""
    if not project_name:
        if yes:
            project_name = default_project_name
        else:
            project_name = (
                input(f"Project name [{default_project_name}]: ").strip()
                or default_project_name
            )

    if args.output_root:
        output_root = Path(args.output_root).expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        return output_root, project_name

    parent_default = args.parent_dir or str(Path.cwd())
    if yes:
        parent_input = parent_default
    else:
        parent_input = (
            input(f"Parent directory [{parent_default}]: ").strip() or parent_default
        )
    parent_dir = Path(parent_input).expanduser().resolve()
    parent_dir.mkdir(parents=True, exist_ok=True)

    output_root = parent_dir / project_name
    if output_root.exists():
        if not yes:
            proceed = input(
                f"Folder already exists: {output_root}. Continue and write files? [y/N]: "
            ).strip().lower()
            if proceed not in {"y", "yes"}:
                raise ValueError("Operation cancelled by user.")
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    return output_root, project_name


def _handle_serve(args: argparse.Namespace) -> None:
    """Handle the 'serve' subcommand — start local web UI."""
    import threading
    import time
    import webbrowser

    import uvicorn

    from project_flow.web.server import app

    port = args.port
    url = f"http://localhost:{port}"

    # Silence all project_flow loggers — the browser UI handles user feedback
    logging.getLogger("project_flow").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

    def _open_browser() -> None:
        time.sleep(1.2)
        webbrowser.open(url)

    if not args.no_browser:
        threading.Thread(target=_open_browser, daemon=True).start()

    print(f"Project Flow running at {url}  (Ctrl+C to stop)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


def _handle_scaffold(args: argparse.Namespace, config) -> None:
    """Handle the 'scaffold' subcommand."""
    output_root, project_name = _resolve_scaffold_output_root(args)
    selected_ides = _collect_selected_ides(args, config)

    project_description = (
        config.project.description
        if config.project.description and config.project.description != UNKNOWN
        else DEFAULT_PROJECT_DESCRIPTION
    )
    config.project.name = project_name
    config.project.description = project_description

    from project_flow.models import TechStackData

    tech_stack = TechStackData(
        project_name=project_name,
        project_description=project_description,
    )
    context = build_generic_context(config, project_name, project_description)
    artifacts = _collect_artifacts(config, selected_ides, tech_stack, context)
    artifacts.extend(generate_planning_stubs(project_name, project_description))

    writer = ArtifactWriter(
        output_root=output_root,
        backup=not args.no_backup,
        dry_run=args.dry_run,
    )
    writer.write_all(artifacts)

    logger.info("\n--- Summary ---")
    logger.info(writer.get_summary())


def _find_tech_stack_content(scan_result: dict, configured_path: str) -> str:
    """Find tech-stack markdown content from scanned repository files."""
    file_contents = scan_result.get("file_contents", {})
    if configured_path and configured_path in file_contents:
        return file_contents[configured_path]

    candidates = []
    configured_name = Path(configured_path).name.lower() if configured_path else ""
    default_name = DEFAULT_PLAN_TECH_STACK_FILE.lower()

    for path, content in file_contents.items():
        name = Path(path).name.lower()
        if name == configured_name or name == default_name:
            candidates.append((path, content))
        elif "tech" in name and "stack" in name and name.endswith(".md"):
            candidates.append((path, content))

    if not candidates:
        return ""

    candidates.sort(key=lambda p: len(Path(p[0]).parts))
    return candidates[0][1]


def _handle_analyze(args: argparse.Namespace, config) -> None:
    """Handle the 'analyze' subcommand."""
    from project_flow.ai_brain import (
        detect_project_name,
        detect_tech_stack,
        generate_rules,
        generate_skills,
    )
    from project_flow.config import get_effective_user_config
    from project_flow.models import TechStackData

    # Default output root to the project path being analyzed
    raw_output = args.output_root if args.output_root and args.output_root != "." else args.path
    output_root = Path(raw_output).expanduser().resolve()
    if not output_root.exists():
        raise FileNotFoundError(f"Output root not found: {output_root}")

    selected_ides = _collect_selected_ides(args, config)
    user_config = get_effective_user_config()

    if not user_config.ai.key or "PLACEHOLDER" in user_config.ai.key:
        raise ValueError(
            "AI API key not configured. The key is managed server-side. "
            "Ensure the Render proxy is running and reachable."
        )

    scan_result = scan_local_project(args.path)
    if not scan_result.get("file_contents"):
        raise ValueError("No project files found for AI analysis.")

    ai_tech_stack = detect_tech_stack(scan_result["file_contents"], user_config)
    ai_project_name, ai_project_desc = detect_project_name(
        scan_result["file_contents"], user_config
    )
    tech_stack_content = _find_tech_stack_content(scan_result, config.project.tech_stack_file)
    parsed_stack = parse_from_string(tech_stack_content) if tech_stack_content else TechStackData()
    ai_rules = generate_rules(ai_tech_stack, user_config, tech_stack_details=parsed_stack.tech_stack_details)
    ai_skills = generate_skills(
        ai_tech_stack,
        config.skills,
        user_config,
        repo_url="",
        tech_stack_details=parsed_stack.tech_stack_details,
    )

    project_name = (
        ai_project_name
        or parsed_stack.project_name
        or config.project.name
        or Path(args.path).name
    )
    project_desc = (
        ai_project_desc
        or parsed_stack.project_description
        or config.project.description
        or DEFAULT_PROJECT_DESCRIPTION
    )

    config.project.name = project_name
    config.project.description = project_desc

    context = build_ai_context(
        config,
        project_name,
        project_desc,
        ai_tech_stack,
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

    artifacts = _collect_artifacts(config, selected_ides, tech_stack, context)

    writer = ArtifactWriter(
        output_root=output_root,
        backup=not args.no_backup,
        dry_run=args.dry_run,
    )
    writer.write_all(artifacts)

    logger.info("\n--- Summary ---")
    logger.info(writer.get_summary())


if __name__ == "__main__":
    main()
