"""AI Brain for Project Flow.

Calls the GLM API to detect tech stack, generate rules, and generate skills.
All prompts come from data/ai-config.json.
All credentials come from runtime config (ai-config.json and/or environment).
"""

import json
import logging

import requests
from jinja2 import Environment

from project_flow.models import DetectedTechStack, UserConfig
from project_flow.utils import (
    load_ai_config,
    load_prompt_file,
    fetch_all_skill_sources,
    fetch_all_rule_sources,
)

logger = logging.getLogger(__name__)


def _get_prompt(prompt_key: str) -> str:
    """Get a prompt template from ai-config.json or files."""
    config = load_ai_config()

    # Check if it's a file reference
    prompt_files = config.get("prompt_files", {})
    if prompt_key == "generate_rules" and "rules" in prompt_files:
        return load_prompt_file(prompt_files["rules"])
    elif prompt_key == "generate_skills" and "skills" in prompt_files:
        return load_prompt_file(prompt_files["skills"])

    # Fall back to embedded prompts
    return config.get("prompts", {}).get(prompt_key, "")


def _call_glm(
    endpoint: str, model: str, key: str, messages: list, max_tokens: int = 2000
) -> str:
    """Make a raw API call to the GLM endpoint.

    Args:
        endpoint: API endpoint URL (from user config).
        model: Model name (from user config).
        key: API key (from user config).
        messages: Chat messages list.
        max_tokens: Maximum tokens in the response (limits reasoning time).

    Returns:
        The response text from the model.

    Raises:
        ValueError: If the API response is malformed or authentication fails.
        ConnectionError: If the API is unreachable.
    """
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    logger.debug("Calling GLM API: %s model=%s", endpoint, model)

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=90)
    except requests.Timeout:
        raise ConnectionError(f"API request timed out after 90s: {endpoint}")
    except requests.ConnectionError:
        raise ConnectionError(f"Cannot connect to API endpoint: {endpoint}")
    except requests.RequestException as e:
        raise ConnectionError(f"API request failed: {e}")

    # Handle HTTP error codes with specific messages
    if response.status_code == 401 or response.status_code == 403:
        raise ValueError(
            f"Authentication failed (HTTP {response.status_code}). "
            "Check your API key in ai-config.json or PROJECT_FLOW_AI_KEY."
        )
    if response.status_code == 429:
        raise ConnectionError("API rate limit exceeded. Please wait and try again.")
    if response.status_code >= 500:
        raise ConnectionError(
            f"API server error (HTTP {response.status_code}). "
            "The service may be temporarily unavailable."
        )
    if response.status_code >= 400:
        raise ValueError(
            f"API request failed with HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )

    # Parse response JSON
    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"API returned invalid JSON: {e}. Response: {response.text[:200]}"
        )

    # Extract content from response
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(
            f"API response has unexpected structure: {e}. "
            f"Response keys: {list(data.keys())}"
        )


def detect_tech_stack(
    file_contents: dict[str, str], user_config: UserConfig
) -> DetectedTechStack:
    """Detect tech stack from project config files using AI.

    Args:
        file_contents: Dict mapping filename to content.
        user_config: User config with AI credentials.

    Returns:
        DetectedTechStack with detected fields.
    """
    if not user_config.ai.key or "PLACEHOLDER" in user_config.ai.key:
        raise ValueError(
            "AI API key not configured. Either:\n"
            "  1. Add a real API key to data/ai-config.json under 'default_api_key', OR\n"
            "  2. Set PROJECT_FLOW_AI_KEY in your environment."
        )
    if not user_config.ai.endpoint:
        raise ValueError("AI endpoint not configured.")

    # Format files for the prompt
    files_text = ""
    for filepath, content in file_contents.items():
        files_text += f"\n--- {filepath} ---\n{content}\n"

    # Get prompt template from config
    prompt_template = _get_prompt("detect_tech_stack")
    prompt = prompt_template.replace("{files}", files_text)

    messages = [{"role": "user", "content": prompt}]
    response_text = _call_glm(
        user_config.ai.endpoint, user_config.ai.model, user_config.ai.key, messages,
        max_tokens=300,
    )

    # Parse JSON from response
    try:
        # Try to extract JSON from the response (may be wrapped in markdown code block)
        json_text = response_text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        data = json.loads(json_text)
    except (json.JSONDecodeError, IndexError):
        logger.warning(
            "Could not parse AI response as JSON. Raw: %s", response_text[:200]
        )
        data = {}

    return DetectedTechStack(
        primary_language=data.get("primary_language", "") or "",
        framework=data.get("framework", "") or "",
        database=data.get("database", "") or "",
        package_manager=data.get("package_manager", "") or "",
        test_framework=data.get("test_framework", "") or "",
        linting=data.get("linting", "") or "",
        formatting=data.get("formatting", "") or "",
        typing=data.get("typing", "") or "",
    )


def detect_project_name(
    file_contents: dict[str, str], user_config: UserConfig
) -> tuple[str, str]:
    """Detect project name and description using AI.

    Returns:
        Tuple of (project_name, project_description).
    """
    if not user_config.ai.key or not user_config.ai.endpoint:
        return ("", "")

    files_text = ""
    for filepath, content in file_contents.items():
        files_text += f"\n--- {filepath} ---\n{content}\n"

    prompt_template = _get_prompt("detect_project_name")
    prompt = prompt_template.replace("{files}", files_text)

    messages = [{"role": "user", "content": prompt}]
    response_text = _call_glm(
        user_config.ai.endpoint, user_config.ai.model, user_config.ai.key, messages,
        max_tokens=150,
    )

    try:
        json_text = response_text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        data = json.loads(json_text)
    except (json.JSONDecodeError, IndexError):
        return ("", "")

    return (data.get("name", ""), data.get("description", ""))


def generate_rules(
    tech_stack: DetectedTechStack,
    user_config: UserConfig,
    tech_stack_details: str = "",
) -> str:
    """Generate project-specific coding rules using AI.

    Args:
        tech_stack: Detected tech stack.
        user_config: User config with AI credentials.
        tech_stack_details: Free-form content from TECH-STACK.md for additional context.

    Returns:
        Markdown string with project-specific rules.
    """
    if not user_config.ai.key or "PLACEHOLDER" in user_config.ai.key:
        return ""

    # Fetch rule sources for additional context
    rule_sources_content = fetch_all_rule_sources()

    tech_summary = json.dumps(
        {
            "language": tech_stack.primary_language,
            "framework": tech_stack.framework,
            "database": tech_stack.database,
            "test_framework": tech_stack.test_framework,
            "linting": tech_stack.linting,
            "formatting": tech_stack.formatting,
        },
        indent=2,
    )

    prompt_template = _get_prompt("generate_rules")
    prompt = Environment().from_string(prompt_template).render(
        tech_stack=tech_summary,
        rule_sources=rule_sources_content or "No additional rule sources available.",
        tech_stack_details=tech_stack_details,
    )

    messages = [{"role": "user", "content": prompt}]
    return _call_glm(
        user_config.ai.endpoint, user_config.ai.model, user_config.ai.key, messages,
        max_tokens=2000,
    )


def generate_skills(
    tech_stack: DetectedTechStack,
    skill_sources: list[dict],
    user_config: UserConfig,
    repo_url: str = "",
    tech_stack_details: str = "",
) -> list[dict]:
    """Generate project-specific skills using AI.

    Args:
        tech_stack: Detected tech stack.
        skill_sources: List of dicts with 'name', 'description', 'source_url'.
        user_config: User config with AI credentials.
        repo_url: Optional repository URL for context.
        tech_stack_details: Free-form content from TECH-STACK.md for additional context.

    Returns:
        List of dicts with 'name', 'description', 'content'.
    """
    if not user_config.ai.key or "PLACEHOLDER" in user_config.ai.key:
        return []

    # Fetch skill sources for additional context
    skill_sources_content = fetch_all_skill_sources()

    tech_summary = json.dumps(
        {
            "language": tech_stack.primary_language,
            "framework": tech_stack.framework,
            "database": tech_stack.database,
        },
        indent=2,
    )

    sources_text = json.dumps(
        [
            {
                "name": s["name"] if isinstance(s, dict) else s.name,
                "description": s["description"] if isinstance(s, dict) else s.description,
            }
            for s in skill_sources
        ],
        indent=2,
    )

    prompt_template = _get_prompt("generate_skills")
    prompt = Environment().from_string(prompt_template).render(
        tech_stack=tech_summary,
        skill_sources=sources_text,
        repo_url=repo_url or "Unknown",
        skill_sources_content=skill_sources_content or "No additional skill sources available.",
        tech_stack_details=tech_stack_details,
    )

    messages = [{"role": "user", "content": prompt}]
    response_text = _call_glm(
        user_config.ai.endpoint, user_config.ai.model, user_config.ai.key, messages,
        max_tokens=2000,
    )

    try:
        json_text = response_text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        return json.loads(json_text)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Could not parse skills response as JSON")
        return []
