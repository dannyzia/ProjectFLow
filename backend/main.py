"""Project Flow API Proxy.

Receives AI requests from the CLI and forwards them to OpenRouter,
injecting the server-side API key. Tries models in order and falls back
to the next if one fails or is rate-limited.
"""

import logging
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Flow API Proxy")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 120

# Models tried in order — first success wins
FALLBACK_MODELS = [
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-120b:free",
    "openrouter/auto",
]


class ChatRequest(BaseModel):
    model: str  # ignored — server controls model selection via fallback list
    messages: list[dict]


@app.get("/health")
def health():
    return {"status": "ok", "configured": bool(OPENROUTER_KEY)}


def _try_model(model: str, messages: list[dict]) -> dict | None:
    """Attempt one model. Returns parsed JSON on success, None on retryable failure."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://project-flow-api.onrender.com",
        "X-Title": "Project Flow",
    }
    payload = {"model": model, "messages": messages}
    try:
        resp = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, timeout=TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as e:
        logger.warning("Model %s network error: %s", model, e)
        return None

    if resp.status_code == 429 or resp.status_code >= 500:
        logger.warning("Model %s returned %s — trying next", model, resp.status_code)
        return None
    if resp.status_code in (401, 403):
        raise HTTPException(status_code=500, detail="OpenRouter API key rejected.")
    if not resp.ok:
        logger.warning("Model %s returned %s — trying next", model, resp.status_code)
        return None
    return resp.json()


@app.post("/proxy")
def proxy_chat(req: ChatRequest):
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured on server.")

    for model in FALLBACK_MODELS:
        result = _try_model(model, req.messages)
        if result is not None:
            return result

    raise HTTPException(status_code=502, detail="All models failed or rate-limited. Try again shortly.")

