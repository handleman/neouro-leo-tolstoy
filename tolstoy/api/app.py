"""Retrieval + chat API: GET /health + POST /search + POST /chat (0009 step 3).

Contract: /health reports {"status", "mode", "collection", "chunk_count",
"embed_model", "ollama_model", "ollama_reachable"}.
POST /search takes {query, collection?, top_k?, filter?} and returns
{collection, results[]} ordered by score desc. POST /chat takes
{question, lang?, chain?, collection?} and returns {answer, answer_lang,
chain, sources[]}. Unknown collections -> 404 "not built yet"; empty
queries -> 422; unknown chain/bad lang -> 422; generator down -> 503.

`embed_query_text` / `run_search_query` / `run_chat_ask` are module-level
indirections so tests can monkeypatch them (no model load in unit tests).
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


class ChatSource(BaseModel):
    chunk_id: str
    volume: int | None = None
    work: str = ""
    chapter: str = ""
    score: float = 0.0


class ChatRequest(BaseModel):
    question: str = ""
    lang: str | None = None
    chain: str | None = None
    collection: str | None = None


class ChatResponse(BaseModel):
    answer: str
    answer_lang: str
    chain: str
    sources: list[ChatSource]


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


def run_chat_ask(chain_name: str, question: str, lang: str, collection: str) -> dict:
    from tolstoy.chains import CHAIN_REGISTRY

    chain_cls = CHAIN_REGISTRY[chain_name]
    return chain_cls(collection=collection).ask(question, lang)


@app.get("/health")
def health() -> dict:
    from tolstoy.generate import ollama
    from tolstoy.store import chroma

    settings = load_settings()
    try:
        count = chroma.collection_count()
    except Exception:
        count = 0
    try:
        reachable = ollama.is_reachable()
    except Exception:
        reachable = False
    return {
        "status": "ok",
        "mode": "retrieval",
        "collection": settings.collection,
        "chunk_count": count,
        "embed_model": settings.embed_model,
        "ollama_model": settings.ollama_model,
        "ollama_reachable": reachable,
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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    from tolstoy.chains import CHAIN_REGISTRY
    from tolstoy.generate.ollama import GeneratorUnavailable
    from tolstoy.store.chroma import NOT_BUILT_YET, CollectionNotBuiltError

    settings = load_settings()
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must be non-empty")
    lang = request.lang or settings.default_lang
    if lang not in ("ru", "en"):
        raise HTTPException(status_code=422, detail="lang must be ru|en")
    chain_name = request.chain or "naive"
    if chain_name not in CHAIN_REGISTRY:
        raise HTTPException(status_code=422, detail=f"unknown chain '{chain_name}'")
    collection = request.collection or settings.collection
    if collection != settings.collection:
        raise HTTPException(status_code=404, detail=f"collection '{collection}' {NOT_BUILT_YET}")

    try:
        result = run_chat_ask(chain_name, question, lang, collection)
    except CollectionNotBuiltError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GeneratorUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ChatResponse(
        answer=result["answer"],
        answer_lang=result["answer_lang"],
        chain=chain_name,
        sources=[ChatSource(**source) for source in result["sources"]],
    )
