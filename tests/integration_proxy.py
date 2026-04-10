#!/usr/bin/env python3
"""Integration test runner for the OpenRouter proxy.

Two modes:
  1. Remote (default) — tests a live deployment, e.g. Render.
     No API key needed locally; the key is already on the server.

       python tests/integration_proxy.py
           uses RENDER_URL env var, or https://project-flow-api.onrender.com

  2. Local — spins up the proxy on port 8081 using a local key.

       PROXY_LOCAL=1 OPENROUTER_API_KEY=sk-or-... python tests/integration_proxy.py

Optional env vars:
    RENDER_URL        Live proxy base URL  (default: https://project-flow-api.onrender.com)
    PROXY_LOCAL       Set to 1 to run locally instead of against Render
    OPENROUTER_API_KEY  Required only in local mode
    PROXY_PORT        Local port  (default 8081)
    PROXY_HOST        Local host  (default 127.0.0.1)
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LOCAL_MODE = os.environ.get("PROXY_LOCAL", "") == "1"

if LOCAL_MODE:
    HOST = os.environ.get("PROXY_HOST", "127.0.0.1")
    PORT = int(os.environ.get("PROXY_PORT", "8081"))
    BASE = f"http://{HOST}:{PORT}"
    KEY = os.environ.get("OPENROUTER_API_KEY", "")
else:
    BASE = os.environ.get("RENDER_URL", "https://project-flow-api.onrender.com").rstrip("/")
    KEY = ""  # key is on Render, not needed locally

BACKEND_DIR = Path(__file__).parent.parent / "backend"
PYTHON = sys.executable

SIMPLE_MESSAGES = [{"role": "user", "content": "Reply with exactly: OK"}]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []


def check(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    status = PASS if passed else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")


def wait_for_server(timeout: int = 10) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health():
    print("\n── Phase 1: Health check ──")
    r = requests.get(f"{BASE}/health", timeout=5)
    check("GET /health returns 200", r.status_code == 200)
    body = r.json()
    check("configured=true with key", body.get("configured") is True, str(body))


def test_first_model():
    print("\n── Phase 2: First model (z-ai/glm-4.5-air:free) ──")
    payload = {"model": "z-ai/glm-4.5-air:free", "messages": SIMPLE_MESSAGES}
    r = requests.post(f"{BASE}/proxy", json=payload, timeout=60)
    check("POST /proxy returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        body = r.json()
        check("Response has choices", "choices" in body)
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        check("Model replied with content", bool(content), repr(content[:80]))
        model_used = body.get("model", "")
        check("Model field present", bool(model_used), model_used)
    else:
        print(f"    Response: {r.text[:200]}")


def test_model_override_ignored():
    print("\n── Phase 3: Client model field is ignored ──")
    payload = {"model": "some-random-model-the-client-chose", "messages": SIMPLE_MESSAGES}
    r = requests.post(f"{BASE}/proxy", json=payload, timeout=60)
    check("Proxy succeeds despite unknown client model", r.status_code == 200, f"status={r.status_code}")


def test_all_models():
    """Try each model individually by temporarily patching the fallback list.

    We can't do this without restarting the server, so instead we test the
    fallback indirectly: we make three rapid requests and confirm they all
    return valid responses (demonstrating the endpoint is stable).
    """
    print("\n── Phase 4: Stability — 3 consecutive requests ──")
    payload = {"model": "any", "messages": SIMPLE_MESSAGES}
    for i in range(1, 4):
        r = requests.post(f"{BASE}/proxy", json=payload, timeout=60)
        check(f"Request {i} succeeds", r.status_code == 200, f"status={r.status_code}")


def test_auth_header_not_exposed():
    """The response must not contain the server key anywhere (local mode only)."""
    print("\n── Phase 5: Key not leaked in response ──")
    if not LOCAL_MODE or not KEY:
        check("Key leak check skipped (remote mode — key not known locally)", True)
        return
    payload = {"model": "any", "messages": SIMPLE_MESSAGES}
    r = requests.post(f"{BASE}/proxy", json=payload, timeout=60)
    if r.status_code == 200:
        check("Server key not in response body", KEY not in r.text)
    else:
        check("Could not test (proxy returned error)", False, f"status={r.status_code}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Project Flow — OpenRouter Proxy Integration Tests ===")

    if LOCAL_MODE:
        if not KEY:
            print("ERROR: OPENROUTER_API_KEY is not set (required for local mode).")
            sys.exit(1)
        print(f"Mode      : LOCAL  ({BASE})")
        print(f"Key       : {KEY[:8]}...{KEY[-4:]}")
        _run_local()
    else:
        print(f"Mode      : REMOTE ({BASE})")
        print("Key       : (on Render — not needed locally)")
        _run_remote()


def _run_remote():
    """Test the live Render deployment directly."""
    print("\nConnecting to Render deployment...")
    try:
        r = requests.get(f"{BASE}/health", timeout=15)
    except requests.ConnectionError as e:
        print(f"ERROR: Could not reach {BASE}\n  {e}")
        sys.exit(1)

    if r.status_code != 200:
        print(f"ERROR: /health returned {r.status_code}")
        sys.exit(1)

    body = r.json()
    configured = body.get("configured", False)
    if not configured:
        print("\nWARNING: Render proxy reports configured=false.")
        print("  The OPENROUTER_API_KEY has not been set in the Render dashboard yet.")
        print("  Go to: Render dashboard → project-flow-api → Environment → add OPENROUTER_API_KEY")
        print("\nSkipping AI call tests — health check only.\n")
        check("GET /health returns 200", True)
        check("configured=false (key not set on Render yet)", False,
              "Set OPENROUTER_API_KEY in Render dashboard and redeploy")
        _print_summary()
        return

    print("Render proxy is up and configured.\n")
    test_health()
    test_first_model()
    test_model_override_ignored()
    test_all_models()
    test_auth_header_not_exposed()
    _print_summary()


def _run_local():
    """Start a local proxy, run tests, then shut it down."""
    print(f"\nStarting proxy server on {BASE}...")
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = KEY
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--host", HOST, "--port", str(PORT), "--log-level", "error"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not wait_for_server():
            print("ERROR: proxy failed to start within 10 seconds")
            proc.terminate()
            sys.exit(1)
        print("Proxy ready.\n")

        test_health()
        test_first_model()
        test_model_override_ignored()
        test_all_models()
        test_auth_header_not_exposed()
    finally:
        proc.terminate()
        proc.wait()

    _print_summary()


def _print_summary():
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("\nFailed tests:")
        for name, ok, detail in results:
            if not ok:
                print(f"  • {name}" + (f" — {detail}" if detail else ""))
        sys.exit(1)
    else:
        print("All integration tests passed.")


if __name__ == "__main__":
    main()
