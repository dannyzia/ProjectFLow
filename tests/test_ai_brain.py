"""Tests for ai_brain.py module."""

import json
from unittest.mock import patch, MagicMock

import pytest
import requests

from project_flow.ai_brain import (
    _call_glm,
    _get_prompt,
    detect_project_name,
    detect_tech_stack,
    generate_rules,
    generate_skills,
)
from project_flow.models import DetectedTechStack, UserAiConfig, UserConfig


def _make_user_config(
    key: str = "test-key",
    endpoint: str = "https://api.test.com/v1",
    model: str = "test-model",
) -> UserConfig:
    return UserConfig(ai=UserAiConfig(key=key, endpoint=endpoint, model=model))


class TestGetPrompt:
    """Tests for prompt loading from ai-config.json."""

    def test_get_existing_prompt(self):
        prompt = _get_prompt("detect_tech_stack")
        assert "files" in prompt.lower() or "tech" in prompt.lower()
        assert len(prompt) > 10

    def test_get_missing_prompt_returns_empty(self):
        prompt = _get_prompt("nonexistent_prompt")
        assert prompt == ""

    def test_get_all_prompts_exist(self):
        for key in [
            "detect_tech_stack",
            "detect_project_name",
            "generate_rules",
            "generate_skills",
        ]:
            prompt = _get_prompt(key)
            assert len(prompt) > 0, f"Prompt '{key}' is empty"


class TestCallGlm:
    """Tests for the _call_glm API call function."""

    @patch("project_flow.ai_brain.requests.post")
    def test_successful_call(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_post.return_value = mock_response

        result = _call_glm("https://api.test.com", "model", "key", [])
        assert result == "Hello!"

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer key"

    @patch("project_flow.ai_brain.requests.post")
    def test_auth_failure_401(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Authentication failed"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_auth_failure_403(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Authentication failed"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_rate_limit_429(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with pytest.raises(ConnectionError, match="rate limit"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_server_error_500(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with pytest.raises(ConnectionError, match="server error"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Connection timed out")

        with pytest.raises(ConnectionError, match="timed out"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_connection_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Cannot connect")

        with pytest.raises(ConnectionError, match="Cannot connect"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_malformed_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"no_choices_key": True}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="unexpected structure"):
            _call_glm("https://api.test.com", "model", "key", [])

    @patch("project_flow.ai_brain.requests.post")
    def test_invalid_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="invalid JSON"):
            _call_glm("https://api.test.com", "model", "key", [])


class TestDetectTechStack:
    """Tests for tech stack detection."""

    def test_missing_credentials_raises(self):
        config = _make_user_config(key="", endpoint="")
        with pytest.raises(ValueError, match="AI API key not configured"):
            detect_tech_stack({"file.py": "content"}, config)

    @patch("project_flow.ai_brain._call_glm")
    def test_successful_detection(self, mock_call):
        mock_call.return_value = json.dumps(
            {
                "primary_language": "Python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "package_manager": "uv",
                "test_framework": "pytest",
                "linting": "ruff",
                "formatting": "black",
                "typing": "mypy",
            }
        )
        config = _make_user_config()
        result = detect_tech_stack(
            {"pyproject.toml": "[project]\nname = 'test'"}, config
        )

        assert result.primary_language == "Python"
        assert result.framework == "FastAPI"
        assert result.database == "PostgreSQL"

    @patch("project_flow.ai_brain._call_glm")
    def test_detection_with_markdown_code_block(self, mock_call):
        mock_call.return_value = (
            '```json\n{"primary_language": "Go", "framework": "Gin"}\n```'
        )
        config = _make_user_config()
        result = detect_tech_stack({"go.mod": "module test"}, config)

        assert result.primary_language == "Go"
        assert result.framework == "Gin"

    @patch("project_flow.ai_brain._call_glm")
    def test_detection_with_malformed_json(self, mock_call):
        mock_call.return_value = "This is not JSON at all"
        config = _make_user_config()
        result = detect_tech_stack({"file.txt": "content"}, config)

        # Should return empty defaults, not crash
        assert result.primary_language == ""
        assert result.framework == ""

    @patch("project_flow.ai_brain._call_glm")
    def test_detection_with_partial_fields(self, mock_call):
        mock_call.return_value = '{"primary_language": "Rust"}'
        config = _make_user_config()
        result = detect_tech_stack({"Cargo.toml": "[package]"}, config)

        assert result.primary_language == "Rust"
        assert result.framework == ""


class TestDetectProjectName:
    """Tests for project name detection."""

    def test_missing_credentials_returns_empty(self):
        config = _make_user_config(key="", endpoint="")
        name, desc = detect_project_name({"file.py": "content"}, config)
        assert name == ""
        assert desc == ""

    @patch("project_flow.ai_brain._call_glm")
    def test_successful_detection(self, mock_call):
        mock_call.return_value = (
            '{"name": "My Project", "description": "A test project"}'
        )
        config = _make_user_config()
        name, desc = detect_project_name(
            {"package.json": '{"name": "my-project"}'}, config
        )

        assert name == "My Project"
        assert desc == "A test project"


class TestGenerateRules:
    """Tests for rules generation."""

    def test_missing_credentials_returns_empty(self):
        config = _make_user_config(key="", endpoint="")
        tech = DetectedTechStack(primary_language="Python")
        result = generate_rules(tech, config)
        assert result == ""

    @patch("project_flow.ai_brain._call_glm")
    def test_successful_generation(self, mock_call):
        mock_call.return_value = "# Coding Rules\n- Use type hints\n- Write tests"
        config = _make_user_config()
        tech = DetectedTechStack(primary_language="Python", framework="FastAPI")
        result = generate_rules(tech, config)

        assert "Coding Rules" in result


class TestGenerateSkills:
    """Tests for skills generation."""

    def test_missing_credentials_returns_empty(self):
        config = _make_user_config(key="", endpoint="")
        tech = DetectedTechStack(primary_language="Python")
        result = generate_skills(tech, [], config)
        assert result == []

    @patch("project_flow.ai_brain._call_glm")
    def test_successful_generation(self, mock_call):
        mock_call.return_value = json.dumps(
            [
                {
                    "name": "testing",
                    "description": "Test skill",
                    "content": "# Testing\nWrite tests.",
                }
            ]
        )
        config = _make_user_config()
        tech = DetectedTechStack(primary_language="Python")
        sources = [
            {
                "name": "testing",
                "description": "Test practices",
                "source_url": "https://example.com",
            }
        ]
        result = generate_skills(tech, sources, config)

        assert len(result) == 1
        assert result[0]["name"] == "testing"

    @patch("project_flow.ai_brain._call_glm")
    def test_malformed_response_returns_empty(self, mock_call):
        mock_call.return_value = "Not JSON at all"
        config = _make_user_config()
        tech = DetectedTechStack(primary_language="Python")
        result = generate_skills(tech, [], config)

        assert result == []
