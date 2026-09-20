"""Phase 0 skeleton API: GET /health only.

Contract: {"status": "ok", "mode": "skeleton", "collection": <name>}.
The `mode` field makes contract evolution explicit: Phase 2 adds store
info, Phase 3 adds Ollama reachability. No Chroma/Ollama contact yet.
"""

from fastapi import FastAPI

from tolstoy.config import load_settings

app = FastAPI(title="cyber-tolstoy")


@app.get("/health")
def health() -> dict:
    settings = load_settings()
    return {
        "status": "ok",
        "mode": "skeleton",
        "collection": settings.collection,
    }
