"""GitHub repository scanner for Project Flow.

Fetches repo tree and file contents via GitHub API.
All file patterns come from data/detection-patterns.json — nothing hardcoded.
"""

import base64
import logging
import re
from fnmatch import fnmatch

import requests

from project_flow.utils import load_detection_patterns

logger = logging.getLogger(__name__)


def parse_repo_url(url: str) -> dict:
    """Parse a GitHub repo URL into owner, repo, host.

    Supports:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - git@github.com:owner/repo.git
      - owner/repo (shorthand)
    """
    # Shorthand: owner/repo
    if "/" in url and "://" not in url and "@" not in url:
        parts = url.strip("/").split("/")
        return {
            "host": "github.com",
            "owner": parts[0],
            "repo": parts[1].removesuffix(".git"),
        }

    # SSH: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@([^:]+):([^/]+)/(.+?)(?:\.git)?$", url)
    if ssh_match:
        return {
            "host": ssh_match.group(1),
            "owner": ssh_match.group(2),
            "repo": ssh_match.group(3),
        }

    # HTTPS: https://github.com/owner/repo(.git)?
    https_match = re.match(r"https?://([^/]+)/([^/]+)/(.+?)(?:\.git)?$", url)
    if https_match:
        return {
            "host": https_match.group(1),
            "owner": https_match.group(2),
            "repo": https_match.group(3),
        }

    raise ValueError(f"Cannot parse repo URL: {url}")


def fetch_repo_tree(
    owner: str, repo: str, token: str = "", branch: str = ""
) -> list[str]:
    """Fetch the full file tree of a GitHub repo.

    Returns a list of file paths (relative to repo root).
    """
    patterns = load_detection_patterns()
    gh_config = patterns.get("github_api", {})
    base_url = gh_config.get("base_url", "https://api.github.com")
    default_branch = branch or gh_config.get("default_branch", "main")
    tree_endpoint = gh_config.get(
        "tree_endpoint", "/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    )

    url = base_url + tree_endpoint.format(owner=owner, repo=repo, branch=default_branch)

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    tree = data.get("tree", [])

    # Only return blobs (files), not trees (directories)
    return [item["path"] for item in tree if item.get("type") == "blob"]


def find_config_files(tree: list[str]) -> list[str]:
    """Find config files in the repo tree using detection-patterns.json.

    Returns matched file paths sorted by priority.
    """
    patterns = load_detection_patterns()

    # Collect all patterns to match against
    all_patterns = []
    for lang_patterns in patterns.get("config_files", {}).values():
        all_patterns.extend(lang_patterns)
    all_patterns.extend(patterns.get("infra_files", []))
    all_patterns.extend(patterns.get("always_fetch", []))

    # Match each file against patterns
    matched = []
    for filepath in tree:
        filename = filepath.rsplit("/", 1)[-1] if "/" in filepath else filepath
        for pattern in all_patterns:
            if fnmatch(filename, pattern) or fnmatch(filepath, pattern):
                matched.append(filepath)
                break

    return matched


def fetch_file_contents(
    owner: str,
    repo: str,
    paths: list[str],
    token: str = "",
    branch: str = "",
) -> dict[str, str]:
    """Fetch file contents from GitHub API.

    Returns a dict mapping file path to decoded content string.
    """
    patterns = load_detection_patterns()
    gh_config = patterns.get("github_api", {})
    base_url = gh_config.get("base_url", "https://api.github.com")
    content_endpoint = gh_config.get(
        "content_endpoint", "/repos/{owner}/{repo}/contents/{path}"
    )
    default_branch = branch or gh_config.get("default_branch", "main")
    max_size = patterns.get("max_file_size_bytes", 1048576)
    max_files = patterns.get("max_files_to_fetch", 20)

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    contents = {}

    for filepath in paths[:max_files]:
        url = base_url + content_endpoint.format(owner=owner, repo=repo, path=filepath)
        if default_branch:
            url += f"?ref={default_branch}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.debug(
                    "Could not fetch %s: HTTP %d", filepath, response.status_code
                )
                continue

            data = response.json()

            # Skip large files
            if data.get("size", 0) > max_size:
                logger.debug("Skipping large file: %s", filepath)
                continue

            # Decode base64 content
            encoded = data.get("content", "")
            if encoded:
                contents[filepath] = base64.b64decode(encoded).decode(
                    "utf-8", errors="replace"
                )

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.warning("Error fetching %s: %s", filepath, e)
            continue

    return contents


def scan_project(repo_url: str, token: str = "") -> dict:
    """Full project scan: fetch tree, find configs, fetch contents.

    Returns:
        {
            "url": str,
            "owner": str,
            "repo": str,
            "tree": list[str],
            "config_files": list[str],
            "file_contents": dict[str, str],
        }
    """
    repo_info = parse_repo_url(repo_url)
    owner = repo_info["owner"]
    repo = repo_info["repo"]

    logger.info("Scanning repo: %s/%s", owner, repo)

    # Step 1: Fetch full tree
    tree = fetch_repo_tree(owner, repo, token=token)
    logger.info("Found %d files in repo tree", len(tree))

    # Step 2: Find config files
    config_files = find_config_files(tree)
    logger.info("Found %d config files", len(config_files))

    # Step 3: Fetch contents
    file_contents = fetch_file_contents(owner, repo, config_files, token=token)
    logger.info("Fetched %d file contents", len(file_contents))

    return {
        "url": repo_url,
        "owner": owner,
        "repo": repo,
        "tree": tree,
        "config_files": config_files,
        "file_contents": file_contents,
    }
