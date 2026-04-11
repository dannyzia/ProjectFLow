"""Tests for the local web server (src/project_flow/web/server.py)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from project_flow.web.server import app

client = TestClient(app)


class TestCwdEndpoint:
    """Tests for GET /api/cwd."""

    def test_returns_cwd(self):
        response = client.get("/api/cwd")
        assert response.status_code == 200
        data = response.json()
        assert "cwd" in data
        assert Path(data["cwd"]).exists()


class TestOpenFolderEndpoint:
    """Tests for GET /api/open-folder."""

    def test_open_existing_folder(self, tmp_path):
        with patch("project_flow.web.server.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            response = client.get(f"/api/open-folder?path={tmp_path}")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_popen.assert_called_once()

    def test_open_nonexistent_folder_returns_404(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        response = client.get(f"/api/open-folder?path={missing}")
        assert response.status_code == 404

    def test_open_folder_missing_path_param_returns_422(self):
        response = client.get("/api/open-folder")
        assert response.status_code == 422


class TestScaffoldEndpoint:
    """Tests for POST /api/scaffold."""

    def _valid_payload(self, output_path: str) -> dict:
        return {
            "project_name": "test-project",
            "project_description": "A test project.",
            "output_path": output_path,
            "ides": ["vscode"],
        }

    def test_scaffold_creates_files(self, tmp_path):
        payload = self._valid_payload(str(tmp_path))
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "files_written" in data
        assert "output_path" in data
        assert data["output_path"] == str(tmp_path)

    def test_scaffold_missing_project_name_returns_422(self, tmp_path):
        payload = {
            "project_description": "desc",
            "output_path": str(tmp_path),
            "ides": ["vscode"],
        }
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 422

    def test_scaffold_empty_ides_returns_422(self, tmp_path):
        payload = self._valid_payload(str(tmp_path))
        payload["ides"] = []
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 422

    def test_scaffold_invalid_ide_returns_422(self, tmp_path):
        payload = self._valid_payload(str(tmp_path))
        payload["ides"] = ["nonexistent-ide"]
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 422

    def test_scaffold_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "new_project"
        assert not new_dir.exists()
        payload = self._valid_payload(str(new_dir))
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 200
        assert new_dir.exists()

    def test_scaffold_all_ides(self, tmp_path):
        from project_flow.constants import SUPPORTED_IDES
        payload = self._valid_payload(str(tmp_path))
        payload["ides"] = list(SUPPORTED_IDES)
        response = client.post("/api/scaffold", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["files_written"]) > 0


class TestAnalyzeEndpoint:
    """Tests for POST /api/analyze."""

    def test_analyze_missing_project_path_returns_422(self):
        payload = {"ides": ["vscode"]}
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_nonexistent_path_returns_422(self, tmp_path):
        payload = {
            "project_path": str(tmp_path / "no_such_folder"),
            "ides": ["vscode"],
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_invalid_ide_returns_422(self, tmp_path):
        payload = {
            "project_path": str(tmp_path),
            "ides": ["not-real"],
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_empty_ides_returns_422(self, tmp_path):
        payload = {
            "project_path": str(tmp_path),
            "ides": [],
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_no_ai_key_returns_503(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        payload = {"project_path": str(tmp_path), "ides": ["vscode"]}
        mock_config = MagicMock()
        mock_config.ai.key = "PLACEHOLDER"
        with patch("project_flow.web.server.get_effective_user_config", return_value=mock_config):
            response = client.post("/api/analyze", json=payload)
        assert response.status_code == 503

    def test_analyze_ai_connection_error_returns_503(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        payload = {"project_path": str(tmp_path), "ides": ["vscode"]}
        mock_config = MagicMock()
        mock_config.ai.key = "real-key"
        with (
            patch("project_flow.web.server.get_effective_user_config", return_value=mock_config),
            patch("project_flow.ai_brain.detect_tech_stack", side_effect=ConnectionError("Render timed out")),
        ):
            response = client.post("/api/analyze", json=payload)
        assert response.status_code == 503
        assert "Render timed out" in response.json()["detail"]

    def test_analyze_ai_value_error_returns_503(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        payload = {"project_path": str(tmp_path), "ides": ["vscode"]}
        mock_config = MagicMock()
        mock_config.ai.key = "real-key"
        with (
            patch("project_flow.web.server.get_effective_user_config", return_value=mock_config),
            patch("project_flow.ai_brain.detect_tech_stack", side_effect=ValueError("Invalid API response")),
        ):
            response = client.post("/api/analyze", json=payload)
        assert response.status_code == 503
        assert "Invalid API response" in response.json()["detail"]
