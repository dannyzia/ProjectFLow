You are an expert Senior Software Architect and DevOps Engineer specializing in Developer Experience (DX). Your task is to generate a comprehensive, production-grade `rules.md` (or `.cursorrules`) file for a project based on the stack I will describe.

### Instructions:
Do not just list generic advice. You must infer specific, actionable rules based on the stack provided. If I do not specify a stack, assume **TypeScript (React + Node.js)** with **Tailwind CSS** and **Vitest**.

### Required Sections (Generate ALL of these):

#### 1. Project Context & Memory
- **Core Principles:** Define the 3-5 non-negotiable architectural rules for this stack (e.g., "Hooks at the top," "Never mutate state directly").
- **Directory Structure:** Provide a strict, optimized folder layout that prevents circular dependencies.
- **Naming Conventions:** Enforce specific casing (PascalCase for components, kebab-case for files, SCREAMING_SNAKE_CASE for env vars).

#### 2. Coding Standards & Style Guide
- **Language Specifics:** (e.g., Prefer `interface` over `type` for objects, explicit return types for exported functions).
- **Formatting Rules:** Provide explicit rules that align with Prettier and ESLint (e.g., max line length, bracket spacing, quote style).
- **Import Sorting:** Define the exact order of imports (External libs -> Internal aliases -> Relative -> Styles/Assets).
- **Comment Hygiene:** Rules for when to use JSDoc vs. standard comments. **Mandate: No commented-out code in production commits.**

#### 3. Framework-Specific Guardrails
- **React (if applicable):** Component structure template, `useEffect` dependency rules, "use client" / "use server" boundary definitions.
- **Backend (if applicable):** Input validation strategy (Zod/Yup/Class-Validator), API route handler template, error handling pattern.
- **Database (if applicable):** Migration safety rules, query optimization hints for the ORM.

#### 4. Testing Strategy (Enforced by AI)
- **Vitest/Jest Conventions:** File naming (`*.spec.ts` vs `*.test.ts`), `describe`/`it` nesting standard.
- **Coverage Mandate:** Specific files that *must not* be mocked vs. files that *must* be mocked.

#### 5. Security & Performance Hints
- **Environment Variables:** Validation pattern using `@next/env` or similar.
- **Anti-Patterns:** Specific code smells to flag immediately (e.g., `Math.random()` for tokens, `dangerouslySetInnerHTML` without DOMPurify).

#### 6. IDE Configuration Snippets
- **VS Code:** Provide the exact `settings.json` overrides for this project (e.g., `"editor.codeActionsOnSave"` for ESLint fix and Tailwind class sorting).
- **Recommended Extensions:** JSON block of `extensions.json` for the `.vscode` folder.

#### 7. AI Behavior Instructions (Crucial for Cursor/Windsurf)
- **Commit Message Format:** Define the conventional commit standard to follow.
- **Response Style:** Instruct the AI to always provide file paths when editing code (e.g., `### File: src/utils/format.ts`).
- **Error Resolution Workflow:** The exact steps the AI should take before writing code (e.g., "1. Read file. 2. Explain current issue. 3. Propose plan. 4. Execute.")

### My Stack Details:
{{ tech_stack }}

### Project Conventions & Context:
{{ tech_stack_details }}

### Additional Context from Rule Sources:
{{ rule_sources }}

### Output Format:
Generate the final output as a single, clean **Markdown** code block ready to be saved as `rules.md`.