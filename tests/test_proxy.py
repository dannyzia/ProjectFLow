"""Unit tests for backend/main.py (OpenRouter proxy + fallback chain).

All OpenRouter HTTP calls are mocked with unittest.mock.patch so no real
API key is required.  Run with:

    venv/bin/pytest tests/test_proxy.py -v
"""

import importlib
import sys
import types
import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers to load backend/main.py as a module regardless of package layout
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).parent.parent / "backend"


def _load_backend(env_overrides: dict | None = None):
    """Import backend/main.py with optional env-var overrides.

    Returns the module object fresh every time so tests are isolated.
    """
    # Remove any cached version so env changes take effect
    sys.modules.pop("main", None)

    env = env_overrides or {}
    with patch.dict("os.environ", env, clear=False):
        spec = importlib.util.spec_from_file_location("main", BACKEND_DIR / "main.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["main"] = mod
        spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def backend_with_key():
    """Backend loaded with a fake OpenRouter key set."""
    return _load_backend({"OPENROUTER_API_KEY": "test-key-123"})


@pytest.fixture()
def backend_no_key():
    """Backend loaded with NO OpenRouter key."""
    env = {"OPENROUTER_API_KEY": ""}
    return _load_backend(env)


@pytest.fixture()
def client_with_key(backend_with_key):
    from fastapi.testclient import TestClient
    return TestClient(backend_with_key.app)


@pytest.fixture()
def client_no_key(backend_no_key):
    from fastapi.testclient import TestClient
    return TestClient(backend_no_key.app)


# ---------------------------------------------------------------------------
# /health endpoint
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_with_key(self, client_with_key):
        resp = client_with_key.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["configured"] is True

    def test_health_without_key(self, client_no_key):
        resp = client_no_key.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["configured"] is False


# ---------------------------------------------------------------------------
# _try_model helper
# ---------------------------------------------------------------------------


_GOOD_RESPONSE = {
    "id": "chatcmpl-abc",
    "choices": [{"message": {"role": "assistant", "content": "Hello"}}],
    "model": "z-ai/glm-4.5-air:free",
}

_MESSAGES = [{"role": "user", "content": "hi"}]


class TestTryModel:
    """Test the _try_model() helper in isolation."""

    def _make_mock_resp(self, status_code: int, json_body: dict | None = None):
        m = MagicMock()
        m.status_code = status_code
        m.ok = (200 <= status_code < 300)
        if json_body is not None:
            m.json.return_value = json_body
        return m

    def test_returns_json_on_200(self, backend_with_key):
        mock_resp = self._make_mock_resp(200, _GOOD_RESPONSE)
        with patch("requests.post", return_value=mock_resp):
            result = backend_with_key._try_model("z-ai/glm-4.5-air:free", _MESSAGES)
        assert result == _GOOD_RESPONSE

    def test_returns_none_on_429(self, backend_with_key):
        mock_resp = self._make_mock_resp(429)
        with patch("requests.post", return_value=mock_resp):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None

    def test_returns_none_on_500(self, backend_with_key):
        mock_resp = self._make_mock_resp(500)
        with patch("requests.post", return_value=mock_resp):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None

    def test_returns_none_on_503(self, backend_with_key):
        mock_resp = self._make_mock_resp(503)
        with patch("requests.post", return_value=mock_resp):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None

    def test_returns_none_on_timeout(self, backend_with_key):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.Timeout()):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None

    def test_returns_none_on_connection_error(self, backend_with_key):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.ConnectionError()):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None

    def test_raises_http_exception_on_401(self, backend_with_key):
        from fastapi import HTTPException
        mock_resp = self._make_mock_resp(401)
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                backend_with_key._try_model("some-model", _MESSAGES)
        assert exc_info.value.status_code == 500
        assert "rejected" in exc_info.value.detail.lower()

    def test_raises_http_exception_on_403(self, backend_with_key):
        from fastapi import HTTPException
        mock_resp = self._make_mock_resp(403)
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(HTTPException) as exc_info:
                backend_with_key._try_model("some-model", _MESSAGES)
        assert exc_info.value.status_code == 500

    def test_returns_none_on_other_4xx(self, backend_with_key):
        # e.g. 404 — treated as non-retryable but returns None (not hard fail)
        mock_resp = self._make_mock_resp(404)
        with patch("requests.post", return_value=mock_resp):
            result = backend_with_key._try_model("some-model", _MESSAGES)
        assert result is None


# ---------------------------------------------------------------------------
# /proxy endpoint — fallback chain
# ---------------------------------------------------------------------------


class TestProxyEndpoint:
    """Test the fallback chain through the /proxy route."""

    _PAYLOAD = {"model": "ignored", "messages": _MESSAGES}

    def _make_mock_resp(self, status_code: int, json_body: dict | None = None):
        m = MagicMock()
        m.status_code = status_code
        m.ok = (200 <= status_code < 300)
        if json_body is not None:
            m.json.return_value = json_body
        return m

    def test_returns_502_no_key(self, client_no_key):
        resp = client_no_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 500
        assert "OPENROUTER_API_KEY" in resp.json()["detail"]

    def test_first_model_succeeds(self, client_with_key, backend_with_key):
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        with patch("requests.post", return_value=good):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 200
        assert resp.json() == _GOOD_RESPONSE

    def test_falls_back_to_second_when_first_429(self, client_with_key, backend_with_key):
        rate_limited = self._make_mock_resp(429)
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return rate_limited
            return good

        with patch("requests.post", side_effect=side_effect):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 200
        assert call_count["n"] == 2  # tried two models

    def test_falls_back_to_third_when_first_two_fail(self, client_with_key, backend_with_key):
        fail = self._make_mock_resp(500)
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 3:
                return fail
            return good

        with patch("requests.post", side_effect=side_effect):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 200
        assert call_count["n"] == 3  # tried all three

    def test_returns_502_when_all_models_fail(self, client_with_key, backend_with_key):
        fail = self._make_mock_resp(429)
        with patch("requests.post", return_value=fail):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 502
        assert "All models failed" in resp.json()["detail"]

    def test_returns_500_on_key_rejection(self, client_with_key, backend_with_key):
        rejected = self._make_mock_resp(401)
        with patch("requests.post", return_value=rejected):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 500

    def test_fallback_on_network_error(self, client_with_key, backend_with_key):
        import requests as req_lib
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise req_lib.ConnectionError("network down")
            return good

        with patch("requests.post", side_effect=side_effect):
            resp = client_with_key.post("/proxy", json=self._PAYLOAD)
        assert resp.status_code == 200
        assert call_count["n"] == 2

    def test_payload_messages_forwarded(self, client_with_key, backend_with_key):
        """Verify the messages list is passed through to OpenRouter."""
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        captured = {}

        def capture(*args, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return good

        with patch("requests.post", side_effect=capture):
            client_with_key.post("/proxy", json=self._PAYLOAD)

        assert captured["json"]["messages"] == _MESSAGES

    def test_model_overridden_by_server(self, client_with_key, backend_with_key):
        """Client model field is ignored — server uses FALLBACK_MODELS list."""
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        captured = {}

        def capture(*args, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return good

        with patch("requests.post", side_effect=capture):
            client_with_key.post("/proxy", json={"model": "client-chosen-model", "messages": _MESSAGES})

        # The model sent to OpenRouter must be the first FALLBACK_MODELS entry
        assert captured["json"]["model"] == backend_with_key.FALLBACK_MODELS[0]

    def test_authorization_header_set(self, client_with_key, backend_with_key):
        """Verify the Bearer token is the server-side key, not the client's."""
        good = self._make_mock_resp(200, _GOOD_RESPONSE)
        captured = {}

        def capture(*args, **kwargs):
            captured["headers"] = kwargs.get("headers", {})
            return good

        with patch("requests.post", side_effect=capture):
            client_with_key.post("/proxy", json=self._PAYLOAD)

        assert captured["headers"]["Authorization"] == "Bearer test-key-123"
