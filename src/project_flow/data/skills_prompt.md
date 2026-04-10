You are an expert software engineer. Generate 3–5 project‑specific skills in the standard SKILL.md format (YAML frontmatter with name, description, triggers, then numbered steps, ending with a "Why:" line).

## Project Context
- Repository: {{ repo_url }}
- Primary tech stack: {{ tech_stack }}

{{ tech_stack_details }}

## Additional Context from Skill Sources:
{{ skill_sources }}

## Output Rules
1. **Only generate a skill if you are confident it would be triggered at least weekly** in a typical sprint. If you cannot, output a placeholder with a TODO explaining what information is missing (e.g., file paths, error patterns, etc.).
2. **Trigger phrases:** 3–5 natural developer phrases per skill, including at least one question form (e.g., "Why is this query slow?").
3. **Reference specific documentation sections** where relevant (e.g., "See README section 'Migration Workflow', step 3").
4. **Note dependencies** between skills (e.g., "This skill calls the `test‑generator` skill after fixing code").
5. **Rank skills by estimated weekly trigger frequency** – highest first.

## Example: Too Generic (DO NOT DO)
❌ `name: fix-bugs` – triggers: ["fix this bug"] – steps: "1. Find bug 2. Fix it" – Why: "Bugs are bad"  
→ No project-specific paths, no real steps, no value.

## Example: Appropriately Specific (DO THIS)
✅ `name: resolve-sla-miss` – triggers: ["SLA violation", "missed deadline on ticket #", "why is this late"] – steps: "1. Check `sla_policies` collection in MongoDB 2. Compare `updated_at` against `sla_deadline` using `scripts/check_sla.py` 3. If drift >5%, run `fix_sla_timers` script (see runbook section 4.2) 4. Log to `#sla-alerts`" – Why: "SLA misses cost $500 per incident; this skill cuts diagnosis from 30min to 2min."

## Output Format
For each skill, provide a code block with filename like `# SKILL: resolve-sla-miss` followed by the SKILL.md content.