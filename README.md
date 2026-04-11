# Project Flow — AI-Ready Project Scaffolder

**Project Flow** is a Python CLI tool that generates AI-assistant configuration files for your project across multiple IDEs and development environments. Define your agents, prompts, and skills once in YAML, then automatically generate optimized configurations for:

- **GitHub Copilot** (VS Code)
- **Kilo Code**
- **Cursor**
- **Windsurf**
- **Zed**
- **Void**
- **Cline**
- **Claude Code**
- **Antigravity**

## Features

✨ **Multi-IDE Support** — Generate configurations for 9 different AI IDEs from a single config  
🔧 **Configuration-Driven** — Define agents, prompts, and skills once in YAML  
🤖 **Agent-Based System** — Specialized agents for code review, testing, documentation, debugging, and more  
📝 **Template Rendering** — Jinja2-based templates with full variable substitution  
🛡️ **Safe File Writing** — Atomic staging, automatic backups, path security, cross-platform line endings  
🔄 **JSON Merge** — Non-destructive updates to existing configuration files  
🎯 **Dry-Run Mode** — Preview changes without writing files  
⚡ **Fast & Incremental** — Only modifies files that changed, automatic skipping of unchanged files  

## Installation

### One-command install (recommended)

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/dannyzia/ProjectFLow/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/dannyzia/ProjectFLow/main/install.ps1 | iex
```

The script auto-detects your OS, installs into an isolated environment (no admin rights needed on most systems), and adds `project-flow` to your PATH.  Restart your terminal after install if the command isn't found immediately.

### Requirements

- Python 3.11 or higher

### Verify Installation

```bash
project-flow --version
# Output: project-flow 1.0.0
```

## Quick Start

### 1. Copy the Config Template

```bash
# Create a new project directory
mkdir my-ai-ready-project
cd my-ai-ready-project

# Copy the project-flow.yml template from the cloned repo
cp /path/to/project-flow/project-flow.yml .
```

### 2. Configure Your Project

Edit `project-flow.yml`:

```yaml
version: "1.0"

project:
  name: "My AI-Ready Project"
  description: "A project with intelligent AI assistants"
  tech_stack_file: "docs/TECH-STACK.md"
  planning_docs:
    - "docs/README.md"
  language_globs:
    Python: "**/*.py"
    TypeScript: "**/*.ts"

ides:
  vscode: true
  kilo: false
  cursor: false
  windsurf: false
  zed: false
  void: false
  cline: false
  claude: false
  antigravity: false

agents:
  code-reviewer:
    display_name: "Code Reviewer"
    description: "Reviews code for bugs and improvements"
    prompt_file: "config/agents/code-reviewer.md"
    readonly: true
    tools:
      - "search/codebase"
      - "read/terminalLastCommand"
    models:
      primary: "gpt-4"
      vscode_id: "gpt-4"

prompts:
  - filename: "code-review.prompt.md"
    content: "Review the selected code for bugs and improvements."

skills:
  - name: "testing"
    description: "Testing best practices"
    content: |
      # Testing Skill
      
      Write comprehensive tests for all public APIs.
```

### 3. Create Tech Stack File (Optional)

Create `docs/TECH-STACK.md`:

```markdown
# Technology Stack

## Framework
Next.js 13 with TypeScript

## Database
PostgreSQL with Prisma ORM

## Testing
Jest with React Testing Library

## Deployment
Vercel
```

### 4. Scaffold Your Project

```bash
# Preview changes
project-flow scaffold --repo https://github.com/user/repo --dry-run

# Scaffold with defaults (no prompts)
project-flow scaffold --repo https://github.com/user/repo --yes --output-root .

# Scaffold for all enabled IDEs
project-flow scaffold --repo https://github.com/user/repo --all --yes --output-root .
```

### 5. Review Generated Files

Generated files appear in:
- `.github/agents/` — Per-agent configuration (14 files)
- `.github/skills/` — Shared skills
- `.github/prompts/` — Prompt templates
- `.github/copilot-instructions.md` — Main instructions
- `.vscode/settings.json` — VS Code specific settings
- `.kilo/` — Kilo Code configuration
- `.cursor/` — Cursor configuration
- `.windsurf/` — Windsurf configuration
- `.zed/` — Zed configuration
- `.void/` — Void configuration
- `.cline/` — Cline configuration
- `.claude/` — Claude Code configuration

## Configuration Guide

### Project Section

```yaml
project:
  name: String                      # Project name (used in templates)
  description: String               # Project description
  tech_stack_file: String           # Path to tech stack file (relative to output_root)
  output_root: String               # Output directory (default: .)
  planning_docs:                    # Files to include in generation context
    - String                        # Relative paths to documentation files
  language_globs:                   # File patterns per language
    {LANGUAGE}: String              # Example: Python: "**/*.py"
```

### IDEs Section

Enable/disable generation for each IDE:

```yaml
ides:
  vscode: boolean        # GitHub Copilot (VS Code)
  kilo: boolean          # Kilo Code
  cursor: boolean        # Cursor Editor
  windsurf: boolean      # Windsurf
  zed: boolean           # Zed Editor
  void: boolean          # Void
  cline: boolean         # Cline
  claude: boolean        # Claude Code
  antigravity: boolean   # Antigravity
```

### Agents Section

Define specialized AI agents:

```yaml
agents:
  {agent_slug}:
    display_name: String           # Display name for UI
    description: String            # Agent description
    prompt_file: String            # Path to agent's system prompt
    readonly: boolean              # Read-only in some IDEs
    tools:                         # Available tools/capabilities
      - String                     # e.g., "search/codebase", "edit", etc.
    models:
      primary: String              # Default LLM model
      vscode_id: String            # VS Code specific model ID
      kilo_id: String              # Kilo Code specific model ID
    handoffs:                       # Hand off to other agents
      - label: String              # Button label
        agent_slug: String         # Target agent
        send_immediately: boolean  # Auto-handoff
    kilo:                          # Kilo-specific metadata
      color: String                # Agent color (#RRGGBB or named)
      mode: String                 # Kilo mode
```

### Prompts Section

Define reusable prompt templates:

```yaml
prompts:
  - filename: String               # Output filename
    content: String                # Markdown content (supports {{variables}})
```

### Skills Section

Define shared capabilities and best practices:

```yaml
skills:
  - name: String                   # Skill name
    description: String            # Skill description
    content: String                # Markdown content (supports {{variables}})
```

## CLI Commands

### scaffold

Generate generic project scaffold artifacts from a YAML config:

```
project-flow scaffold --repo <url> [OPTIONS]

Options:
  --repo URL            GitHub repo URL to scan (required)
  --ides LIST           Comma-separated IDE list (e.g. vscode,cursor).
                        If omitted, uses config-enabled IDEs.
  --all                 Generate for all 9 supported IDEs
  --project-name NAME   Project name. If omitted, prompted interactively.
  --parent-dir DIR      Parent directory where the project folder will be created.
  --output-root PATH    Explicit output path (skips interactive prompt).
  --dry-run             Preview changes without writing files
  --no-backup           Don't create timestamped backups
  --yes, -y             Non-interactive: accept all defaults without prompting
  --config FILE         Config file path (default: project-flow.yml)
  --verbose, -v         Enable verbose/debug output
  --quiet, -q           Suppress output except errors
```

Examples:

```bash
# Interactive scaffold (prompts for project name and directory)
project-flow scaffold --repo https://github.com/user/repo

# Non-interactive scaffold into current directory
project-flow scaffold --repo https://github.com/user/repo --yes --output-root .

# Specific IDEs with dry-run preview
project-flow scaffold --repo https://github.com/user/repo --ides vscode,cursor --dry-run

# All IDEs, custom output
project-flow scaffold --repo https://github.com/user/repo --all --output-root /path/to/project
```

### analyze

Run AI analysis on a repository and generate project-specific artifacts:

```
project-flow analyze --repo <url> [OPTIONS]

Options:
  --repo URL            GitHub repo URL to scan (required)
  --github-token TOKEN  GitHub API token for private repos
  --ides LIST           Comma-separated IDE list (e.g. vscode,cursor).
                        If omitted, uses config-enabled IDEs.
  --all                 Generate for all 9 supported IDEs
  --output-root PATH    Root directory of the target project (default: .)
  --dry-run             Preview changes without writing files
  --no-backup           Don't create timestamped backups
  --config FILE         Config file path (default: project-flow.yml)
  --verbose, -v         Enable verbose/debug output
  --quiet, -q           Suppress output except errors
```

Examples:

```bash
# Analyze a public repo and write to current directory
project-flow analyze --repo https://github.com/user/repo --output-root .

# Analyze a private repo with token
project-flow analyze --repo https://github.com/user/private-repo --github-token $GITHUB_TOKEN --output-root .

# Dry-run for specific IDEs
project-flow analyze --repo https://github.com/user/repo --ides vscode,cursor --dry-run
```

## Usage Examples

### Example 1: Basic VS Code Setup

```bash
# Create project-flow.yml
cat > project-flow.yml << 'EOF'
version: "1.0"
project:
  name: "My Project"
  description: "An AI-ready project"
  tech_stack_file: "TECH-STACK.md"

ides:
  vscode: true
  kilo: false
  cursor: false
  windsurf: false
  zed: false
  void: false
  cline: false
  claude: false
  antigravity: false

agents:
  reviewer:
    display_name: "Code Reviewer"
    description: "Reviews code"
    prompt_file: "prompts/reviewer.md"
    readonly: true
    tools: []
    models:
      primary: "gpt-4"
      vscode_id: "gpt-4"

prompts:
  - filename: "review.prompt.md"
    content: "Review this code carefully."
EOF

# Scaffold
project-flow scaffold --repo https://github.com/user/repo --yes --output-root .
```

### Example 2: Multi-IDE Setup

```bash
# Scaffold for all IDEs
project-flow scaffold --repo https://github.com/user/repo --all --yes --output-root .

# Or for specific IDEs
project-flow scaffold --repo https://github.com/user/repo --ides vscode,cursor,cline --yes --output-root .
```

### Example 3: Preview and Incremental Updates

```bash
# First, preview what will be generated
project-flow scaffold --repo https://github.com/user/repo --all --dry-run

# Generate for real
project-flow scaffold --repo https://github.com/user/repo --all --yes --output-root .

# Output shows created files
# [CREATE] .github/agents/code-reviewer.md
# [CREATE] .github/skills/testing/SKILL.md
# --- Summary ---
# Files created: 23
# Files updated: 0
# Files skipped (unchanged): 0

# Run again — unchanged files are skipped
project-flow scaffold --repo https://github.com/user/repo --all --yes --output-root .
# [SKIP] .github/agents/code-reviewer.md — unchanged
# [SKIP] .github/skills/testing/SKILL.md — unchanged
```

## Template Variables

Project Flow supports these variables in prompt and skill content:

- `{{ PROJECT_NAME }}` — Project name from config
- `{{ PROJECT_DESCRIPTION }}` — Project description
- `{{ PRIMARY_LANGUAGE }}` — Primary programming language
- `{{ FRAMEWORK }}` — Framework name
- `{{ DATABASE }}` — Database system
- `{{ TEST_FRAMEWORK }}` — Testing framework
- `{{ version }}` — Project Flow version

Example:

```markdown
# {{ PROJECT_NAME }} Code Review Guidelines

We use {{ PRIMARY_LANGUAGE }} with {{ FRAMEWORK }}.
Our test framework is {{ TEST_FRAMEWORK }}.

Focus on:
- Performance in {{ PRIMARY_LANGUAGE }}
- Best practices for {{ FRAMEWORK }}
```

## Artifacts Generated

### Artifact Breakdown by IDE

| IDE | Contents |
|-----|----------|
| VS Code | Agents + instructions + skills + prompts + settings.json |
| Kilo Code | Agent files + kilo.jsonc config |
| Cursor | .cursorrules + scoped .mdc rule files |
| Windsurf | .windsurfrules |
| Zed | settings.json (JSON merge) + project-context.md |
| Void | rules.md + agent-specific files |
| Cline | Agent configuration files |
| Claude Code | Agent configuration files |
| Antigravity | Agent configuration files |

## Advanced Topics

### Extending with Custom Generators

To add support for a new IDE:

1. Create `src/project_flow/generators/{ide_name}.py`
2. Implement `generate(config, tech_stack, context) -> list[Artifact]`
3. Register in `src/project_flow/generators/registry.py`
4. Add CLI flag in `src/project_flow/cli.py`

### JSON Merge Mode

For settings files that should be merged rather than replaced:

```python
artifacts.append(Artifact(
    path=".zed/settings.json",
    content=json.dumps({"key": "value"}),
    mode="json_merge",  # Key: triggers JSON merge
    source="zed",
))
```

This will:
1. Read existing `.zed/settings.json` if it exists
2. Deep-merge new settings into existing settings
3. Preserve existing keys not in the new settings
4. Only write if content actually changed

### Path Security

Project Flow validates all file paths to prevent directory traversal:

```python
# These paths are rejected:
# - "../../escape.txt"
# - "/etc/passwd"
# - "../../../etc/hosts"

# These paths are allowed:
# - "file.txt"
# - "subdirectory/file.txt"
# - ".github/agents/file.md"
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_writer.py -v

# Run with coverage
pytest tests/ --cov=src/project_flow --cov-report=html
```

## Troubleshooting

### Config File Not Found

```
ERROR: Config file not found: project-flow.yml
```

**Solution:** Create the file or use `--config`:

```bash
project-flow scaffold --repo https://github.com/user/repo --config /path/to/config.yml
```

### Invalid Config Version

```
CONFIG ERROR: Invalid config version: 2.0. Expected 1.0
```

**Solution:** Update `version: "1.0"` in your config file.

### Path Conflicts

```
Path conflicts detected between generators:
  .github/config.md — written by both vscode and cursor
```

**Solution:** Ensure each generator writes to unique paths. Check agent slugs and output paths for overlaps.

### Permission Denied

```
ERROR: Permission denied when writing .github/agents/file.md
```

**Solution:** Ensure write permissions for output directory:

```bash
chmod 755 .github
project-flow scaffold --repo https://github.com/user/repo --all --yes --output-root .
```

## Performance Notes

- **Fast generation:** Generates artifacts in < 1 second
- **Incremental updates:** Compares content before writing
- **Automatic skipping:** Re-running skips unchanged files
- **Atomic operations:** All-or-nothing writes prevent partial failures
- **Backup support:** Timestamped backups kept before overwrites

## File Structure

```
project-flow/
├── src/project_flow/
│   ├── __init__.py                # Package initialization
│   ├── cli.py                     # CLI entry point and subcommands
│   ├── config.py                  # Configuration file loading and parsing
│   ├── context.py                 # Template context generation
│   ├── models.py                  # Dataclasses for config and artifacts
│   ├── tech_stack.py              # Tech stack parsing from Markdown
│   ├── writer.py                  # Atomic file writing with staging
│   ├── generators/
│   │   ├── registry.py            # Generator registry (lazy loading)
│   │   ├── vscode.py              # VS Code/GitHub Copilot generator
│   │   ├── kilo.py                # Kilo Code generator
│   │   ├── cursor.py              # Cursor IDE generator
│   │   ├── windsurf.py            # Windsurf generator
│   │   ├── zed.py                 # Zed editor generator
│   │   └── void_gen.py            # Void generator
│   ├── renderers/
│   │   ├── agents.py              # Agent file rendering
│   │   ├── rules.py               # Rules/instructions rendering
│   │   └── skills.py              # Skills rendering
│   └── templates/
│       ├── agent.md.j2            # Agent template
│       ├── instructions.md.j2     # Instructions template
│       ├── skill.md.j2            # Skill template
│       ├── cursor_rule.mdc.j2     # Cursor rule template
│       └── prompt.md.j2           # Prompt template
├── tests/
│   ├── conftest.py                # Pytest fixtures
│   ├── test_config.py             # Configuration tests
│   ├── test_writer.py             # Writer tests
│   ├── test_renderers.py          # Renderer tests
│   ├── test_tech_stack.py         # Tech stack parser tests
│   └── test_e2e.py                # End-to-end tests
├── project-flow.yml               # Example configuration
├── pyproject.toml                 # Package metadata and dependencies
├── README.md                      # This file
└── LICENSE
```

## Development

### Setting Up Development Environment

```bash
git clone <repository-url>
cd project-flow
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Watch mode (requires pytest-watch)
ptw tests/

# Coverage report
pytest tests/ --cov=src/project_flow --cov-report=html
```

### Building Distribution

```bash
pip install build
python -m build
twine upload dist/*
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT License — see LICENSE file for details

## Support

- 📚 [Documentation](./docs/)
- 🐛 Report Issues — open an issue on the repository
- 💬 Discussions — use the repository discussions
- 📧 [Email Support](mailto:support@example.com)

---

**Made with ❤️ for AI-assisted development**

*Project Flow v0.1.0 — Built for developers who want AI assistants that understand their codebase.*