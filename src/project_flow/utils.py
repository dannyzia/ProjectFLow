"""Shared utility functions for Project Flow.

Centralized data-file loaders with module-level caching.
Each JSON data file is read from disk exactly once per process.
"""

import json
from functools import lru_cache
from pathlib import Path

from project_flow.constants import DEFAULT_ENCODING

_DATA_DIR = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def _load_ide_paths_full() -> dict:
    """Load the entire ide-paths.json and cache it. Called once per process."""
    data_file = _DATA_DIR / "ide-paths.json"
    with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


def load_ide_paths(ide_name: str) -> dict:
    """Load path configuration for a specific IDE from ide-paths.json.

    The full JSON file is read from disk exactly once (cached by
    _load_ide_paths_full). Subsequent calls with different ide_name
    values do NOT re-read the file.

    Args:
        ide_name: IDE name key (e.g. 'vscode', 'kilo', 'cursor').

    Returns:
        Dict of path templates and flags for the requested IDE.
        Returns empty dict if IDE name not found.
    """
    return _load_ide_paths_full().get(ide_name, {})


def load_all_ide_paths() -> dict:
    """Load the entire ide-paths.json. Returns the full dict.

    Delegates to the same cached loader used by load_ide_paths.
    """
    return _load_ide_paths_full()


@lru_cache(maxsize=1)
def load_detection_patterns() -> dict:
    """Load detection patterns from data/detection-patterns.json."""
    data_file = _DATA_DIR / "detection-patterns.json"
    with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_ai_config() -> dict:
    """Load AI configuration from data/ai-config.json."""
    data_file = _DATA_DIR / "ai-config.json"
    with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_prompt_file(filename: str) -> str:
    """Load a prompt file from the data directory.

    Args:
        filename: Name of the prompt file (e.g., 'rules_prompt.md').

    Returns:
        The file content as a string.
    """
    data_file = _DATA_DIR / filename
    with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
        return f.read()


@lru_cache(maxsize=1)
def load_source_urls(filename: str) -> list[str]:
    """Load source URLs from a markdown file.

    Parses lines starting with '- https://' from the file.

    Args:
        filename: Name of the source file (e.g., 'skill-sources.md').

    Returns:
        List of URLs found in the file.
    """
    data_file = _DATA_DIR / filename
    urls = []
    with open(data_file, "r", encoding=DEFAULT_ENCODING) as f:
        for line in f:
            line = line.strip()
            if line.startswith("- https://"):
                url = line[2:].strip()  # Remove the '- ' prefix
                urls.append(url)
    return urls


@lru_cache(maxsize=1)
def _load_source_cache() -> dict:
    """Cache for fetched source content from skill/rule repositories."""
    return {}


def fetch_source_content(url: str, timeout: int = 10) -> str:
    """Fetch content from a URL with caching.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        The fetched content as string, or empty string if failed.
    """
    import requests
    import logging

    logger = logging.getLogger(__name__)
    cache = _load_source_cache()

    # Return cached content if available
    if url in cache:
        return cache[url]

    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "project-flow/1.0 (AI configuration generator)"},
        )
        response.raise_for_status()
        content = response.text[:50000]  # Limit to 50KB per source
        cache[url] = content
        logger.debug("Fetched source content from %s (%d bytes)", url, len(content))
        return content
    except Exception as e:
        logger.warning("Could not fetch source from %s: %s", url, e)
        return ""


@lru_cache(maxsize=1)
def fetch_all_skill_sources() -> str:
    """Fetch and concatenate all skill source content.

    Returns:
        Concatenated content from all configured skill sources.
    """
    ai_config = load_ai_config()
    source_files = ai_config.get("source_files", {})
    filename = source_files.get("skill_sources")
    if not filename:
        return ""

    urls = load_source_urls(filename)

    contents = []
    for url in urls:
        content = fetch_source_content(url)
        if content:
            contents.append(f"--- Source: {url} ---\n{content}")

    return "\n\n".join(contents)


@lru_cache(maxsize=1)
def fetch_all_rule_sources() -> str:
    """Fetch and concatenate all rule source content.

    Returns:
        Concatenated content from all configured rule sources.
    """
    ai_config = load_ai_config()
    source_files = ai_config.get("source_files", {})
    filename = source_files.get("rule_sources")
    if not filename:
        return ""

    urls = load_source_urls(filename)

    contents = []
    for url in urls:
        content = fetch_source_content(url)
        if content:
            contents.append(f"--- Source: {url} ---\n{content}")

    return "\n\n".join(contents)
