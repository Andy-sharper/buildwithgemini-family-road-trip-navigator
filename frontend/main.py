"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Why A2A: agents-cli 1.1.0 (GA) deploys ADK agents to Agent Runtime as A2A agents
and no longer registers the reasoning-engine operation schema the old
`agent_engines.get(...).stream_query()` path relied on (operation_schemas() comes
back empty). The container serves the A2A protocol over the Agent Engine HTTP
passthrough, so this proxy fetches the agent's card and sends messages with the
a2a-sdk client (the same path `agents-cli run --mode a2a` uses). This works for
both A2A and plain ADK 1.1.0 deployments (the container serves A2A either way).

Run:
  pip install -r requirements.txt
  export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
  export AGENT_DIRECTORY="app"   # your agent's app directory (agents-cli-manifest.yaml)
  python main.py                 # -> http://localhost:8080
"""

import os
import re
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from google.protobuf.json_format import ParseDict
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    SendMessageRequest,
    TaskArtifactUpdateEvent,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP
# passthrough. The card lives at the well-known path under this base.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    # Always return JSON so the browser never receives a plain-text 500 page
    # (which shows up in the chat as "Unexpected token 'I', "Internal S"... is
    # not valid JSON"). Any server-side failure now surfaces as a readable
    # message in the chat bubble instead.
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
# Cache the agent card after the first fetch.
_card: AgentCard | None = None


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        data = resp.json()
        data["url"] = A2A_BASE
        _card = ParseDict(data, AgentCard(), ignore_unknown_fields=True)
    return _card


def _extract_parts(parts: list) -> list[dict]:
    """Turn A2A response parts into structured parts for the chat UI."""
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        text = getattr(root, "text", None) or getattr(p, "text", None)
        data = getattr(root, "data", None) or getattr(p, "data", None)
        if text:
            out.append({"kind": "text", "text": text})
        elif data is not None:
            meta = getattr(root, "metadata", None) or getattr(p, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": data})
            elif isinstance(data, dict) and any(k in data for k in ("beginRendering", "surfaceUpdate")):
                out.append({"kind": "a2ui", "data": data})
        else:
            file_obj = getattr(root, "file", None) or getattr(p, "file", None)
            uri = getattr(file_obj, "uri", None) if file_obj else None
            if uri:
                out.append({"kind": "text", "text": uri})
    return out


_TAG_RE = re.compile(r"</?a2a_datapart_json>")


def _parse_raw_part(raw_val: str | bytes) -> dict | None:
    """Extract text or A2UI component data from raw part string or bytes."""
    if isinstance(raw_val, bytes):
        raw_str = raw_val.decode("utf-8", errors="ignore")
    else:
        raw_str = str(raw_val)
    clean = _TAG_RE.sub("", raw_str).strip()
    if not clean:
        return None
    try:
        val = json.loads(clean)
        while isinstance(val, str):
            val = json.loads(val)
        if isinstance(val, dict):
            data_inner = val.get("data")
            meta = val.get("metadata") or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME and data_inner:
                return {"kind": "a2ui", "data": data_inner}
            if isinstance(data_inner, dict) and any(k in data_inner for k in ("beginRendering", "surfaceUpdate")):
                return {"kind": "a2ui", "data": data_inner}
            if any(k in val for k in ("beginRendering", "surfaceUpdate")):
                return {"kind": "a2ui", "data": val}
    except Exception:
        pass
    return {"kind": "text", "text": clean}


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(
            ClientConfig(
                httpx_client=client,
            )
        )
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
            context_id=_contexts.get(user_id),
        )
        send_req = SendMessageRequest(message=msg)

        async for event in a2a_client.send_message(send_req):
            if hasattr(event, "WhichOneof"):
                field = event.WhichOneof("payload")
                if field == "task":
                    if event.task.context_id:
                        _contexts[user_id] = event.task.context_id
                elif field == "artifact_update":
                    if event.artifact_update.context_id:
                        _contexts[user_id] = event.artifact_update.context_id
                    for p in event.artifact_update.artifact.parts:
                        raw_val = getattr(p, "raw", None) or getattr(p, "text", None)
                        if raw_val:
                            parsed = _parse_raw_part(raw_val)
                            if parsed:
                                parts.append(parsed)
                elif field == "status_update":
                    if event.status_update.context_id:
                        _contexts[user_id] = event.status_update.context_id
            elif isinstance(event, tuple):
                task, update = event
                if task is not None and getattr(task, "context_id", None):
                    _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    for p in update.artifact.parts:
                        raw_val = getattr(p, "raw", None) or getattr(p, "text", None)
                        if raw_val:
                            parsed = _parse_raw_part(raw_val)
                            if parsed:
                                parts.append(parsed)

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
