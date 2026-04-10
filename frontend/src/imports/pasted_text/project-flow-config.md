Build a modern web application called "Project Flow".
This app is served from localhost:8080 by a local Python process
installed on the user's machine (like Jupyter Notebook).
It helps developers generate AI assistant config files for their projects.

## Pages / Screens

### 1. Home / Landing
- App name: "Project Flow"
- Tagline: "Generate AI config files for your developer projects."
- One CTA button: "Open Generator →" → navigates to /generate
- Clean hero. Dark theme. No stock photos. Abstract code-pattern background.

### 2. Generator — Mode Selection (/generate)
Before showing the form, ask the user which mode they want:

Two large cards side by side:

Card A — "Quick Scaffold"
  Icon: ⚡
  Title: Quick Scaffold
  Description: "Generate standard AI config files using just a project name
  and description. No code analysis. Done in seconds."
  Button: "Choose Scaffold →"

Card B — "Smart Analyze"
  Icon: 🔍
  Title: Smart Analyze
  Description: "Point to an existing project on your machine.
  AI reads your actual code and generates tailored config files."
  Button: "Choose Analyze →"

### 3A. Scaffold Form (/generate/scaffold)

**Section A — Project Info**
- "Project Name" — text input, required, placeholder: "my-awesome-app"
- "Project Description" — textarea, required, 4 rows,
  placeholder: "A REST API built with FastAPI and PostgreSQL..."

**Section B — Output Folder**
- Label: "Where should the files be written?"
- Text input, required, placeholder: "/Users/john/projects/my-app"
- Subtext: "Type the full path to your project folder. Files will be written there directly."
- A small helper button: "Use current directory" that calls GET /api/cwd and fills the field.

**Section C — Choose Your IDEs**
- Label: "Which AI-powered IDEs do you use? (select all that apply)"
- Grid of 9 toggle cards. Each card: IDE name + icon letter badge.
  The 9 IDEs:
    VS Code, Kilo Code, Cursor, Windsurf, Zed, Void, Cline, Claude Code, Antigravity
- At least one must be selected before submitting.

**Generate Button**
- Full-width primary: "⚡ Generate Files"
- Disabled until Project Name, Output Folder, and at least one IDE are filled.

### 3B. Analyze Form (/generate/analyze)

**Section A — Project Folder**
- Label: "Path to your project"
- Text input, required, placeholder: "/Users/john/projects/my-app"
- Subtext: "AI will read your code files to detect your tech stack and generate tailored configs."
- Small helper button: "Use current directory" → GET /api/cwd

**Section B — Choose Your IDEs** (same grid as above)

**Generate Button**
- Full-width primary: "🔍 Analyze & Generate"
- Disabled until path and at least one IDE are filled.

### 4. Loading State (inline, replaces button area)
Spinner + cycling status messages:
  Scaffold: "Generating rules..." → "Building agent configs..." → "Writing files..."
  Analyze:  "Scanning project files..." → "Detecting tech stack..." → "Generating configs..." → "Writing files..."

### 5. Results Screen (replaces form content after success)
- Large green checkmark
- "✅ Done! Files written to: [the path they entered]"
- A list of files written, grouped by IDE:
  e.g.  ✓ .vscode/instructions.md
        ✓ .cursor/rules.md
- Two buttons:
  - "Generate Another" → resets and goes back to mode selection
  - "Open Folder" → calls GET /api/open-folder?path=... to open in file explorer

### 6. Error State (inline below button)
Red alert box: "Something went wrong: [error detail]. Please try again."
Form stays filled.

### 7. Settings (/settings) — linked from navbar
- "Server Status" — green dot if localhost:8080 is responding, red if not
- "AI Backend" — shows: "Connected to project-flow-api.onrender.com" (read-only)
- No API key field — key is managed server-side

## Design System
- Background: dark navy #0f172a
- Surface cards: #1e293b
- Primary accent: electric blue #3b82f6
- Success: #22c55e
- Error: #ef4444
- Text: white / slate-300
- Font: Inter or system-sans
- Border radius: 12px cards, 8px inputs
- Mobile-first, fully responsive
- Accessible: labels, focus rings, ARIA

## Navigation
- Top navbar: Logo left | "Generator" | "Settings" right
- No auth, no login

## API Contract (all calls go to localhost:8080)

GET  /api/cwd
  Response: { "cwd": "/Users/john/projects" }

POST /api/scaffold   (application/json)
  Body: {
    "project_name": "string",
    "project_description": "string",
    "output_path": "/absolute/path",
    "ides": ["vscode", "cursor"]
  }
  Success 200: {
    "files_written": [".vscode/instructions.md", ".cursor/rules.md"],
    "output_path": "/absolute/path"
  }
  Error 4xx/5xx: { "detail": "error message" }

POST /api/analyze    (application/json)
  Body: {
    "project_path": "/absolute/path",
    "ides": ["vscode", "cursor"]
  }
  Success 200: {
    "files_written": [".vscode/instructions.md"],
    "output_path": "/absolute/path"
  }
  Error 4xx/5xx: { "detail": "error message" }

GET  /api/open-folder?path=/absolute/path
  Opens the folder in the OS file explorer. Response: { "ok": true }

## Tech Stack
React + TypeScript. Tailwind CSS.
API base: always http://localhost:8080 (hardcoded, no env var needed).

## File structure:
frontend/
  src/
    App.tsx
    pages/
      Landing.tsx
      ModeSelect.tsx
      ScaffoldForm.tsx
      AnalyzeForm.tsx
      Results.tsx
      Settings.tsx
    components/
      IdeSelector.tsx
      LoadingState.tsx
      ErrorAlert.tsx
      Navbar.tsx
    api/
      client.ts        ← all fetch calls centralised here
  index.html
  package.json
  tailwind.config.js
  vite.config.ts