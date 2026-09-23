"""Retrieval API: GET /health + POST /search (0008 step 5).

Contract: /health reports {"status", "mode": "retrieval", "collection",
"chunk_count", "embed_model"} (no Ollama fields until Phase 3).
POST /search takes {query, collection?, top_k?, filter?} and returns
{collection, results[]} ordered by score desc. Unknown collections
-> 404 "not built yet"; empty queries -> 422.

`embed_query_text` / `run_search_query` are module-level indirections so
tests can monkeypatch them (no model load in unit tests).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tolstoy.config import load_settings

app = FastAPI(title="cyber-tolstoy")


class SearchFilter(BaseModel):
    volume: int | None = None
    work: str | None = None


class SearchRequest(BaseModel):
    query: str = ""
    collection: str | None = None
    top_k: int = 4
    filter: SearchFilter | None = None


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    volume: int | None = None
    work: str = ""
    chapter: str = ""


class SearchResponse(BaseModel):
    collection: str
    results: list[SearchResult]


def embed_query_text(text: str) -> list[float]:
    from tolstoy.store import embed

    return embed.embed_query(text)


def run_search_query(
    vector: list[float], top_k: int, search_filter: dict | None, collection: str
) -> list[dict]:
    from tolstoy.store import chroma

    return chroma.query_store(
        vector, top_k=top_k, search_filter=search_filter, collection_name=collection
    )


@app.get("/health")
def health() -> dict:
    from tolstoy.store import chroma

    settings = load_settings()
    try:
        count = chroma.collection_count()
    except Exception:
        count = 0
    return {
        "status": "ok",
        "mode": "retrieval",
        "collection": settings.collection,
        "chunk_count": count,
        "embed_model": settings.embed_model,
    }


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    from tolstoy.store.chroma import NOT_BUILT_YET, CollectionNotBuiltError

    settings = load_settings()
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=422, detail="query must be non-empty")
    collection = request.collection or settings.collection
    if collection != settings.collection:
        raise HTTPException(status_code=404, detail=f"collection '{collection}' {NOT_BUILT_YET}")
    top_k = max(1, min(request.top_k, 20))
    search_filter = request.filter.model_dump(exclude_none=True) if request.filter else None

    vector = embed_query_text(query)
    try:
        hits = run_search_query(vector, top_k, search_filter, collection)
    except CollectionNotBuiltError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SearchResponse(
        collection=collection,
        results=[SearchResult(**hit) for hit in hits],
    )
