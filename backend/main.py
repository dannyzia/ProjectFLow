"""Project Flow API Proxy.

Receives AI requests from the CLI and forwards them to the GLM API,
injecting the server-side API key. The key is stored in Render's
environment variables and never shipped with the client code.
"""

import logging
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Flow API Proxy")

GLM_KEY = os.environ.get("GLM_API_KEY", "")
GLM_ENDPOINT = os.environ.get("GLM_ENDPOINT", "https://api.z.ai/api/coding/paas/v4")
GLM_TIMEOUT = 120


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]


@app.get("/health")
def health():
    return {"status": "ok", "configured": bool(GLM_KEY)}


@app.post("/proxy")
def proxy_chat(req: ChatRequest):
    if not GLM_KEY:
        raise HTTPException(
            status_code=500, detail="GLM_API_KEY not configured on server."
        )

    headers = {
        "Authorization": f"Bearer {GLM_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": req.model, "messages": req.messages}

    logger.info("Proxying: model=%s messages=%d", req.model, len(req.messages))

    try:
        response = requests.post(
            GLM_ENDPOINT, json=payload, headers=headers, timeout=GLM_TIMEOUT
        )
    except requests.Timeout:
        raise HTTPException(
            status_code=504, detail=f"GLM API timed out after {GLM_TIMEOUT}s."
        )
    except requests.ConnectionError as e:
        raise HTTPException(
            status_code=502, detail=f"Cannot connect to GLM API: {e}"
        )

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=500, detail="GLM API key rejected by upstream server."
        )
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="GLM API rate limit exceeded.")
    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=f"GLM API returned {response.status_code}: {response.text[:200]}",
        )

    return response.json()
