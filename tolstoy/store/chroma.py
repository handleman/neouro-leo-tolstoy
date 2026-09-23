"""Chroma wrapper: persistent `tolstoy-ru` collection (0008 step 3).

Cosine space; upserts are idempotent on `chunk_id`. Requests for any
collection other than the configured one fail with
`CollectionNotBuiltError("... not built yet")` — the contract for the
deferred `tolstoy-en` (0004).
"""

import chromadb

from tolstoy.config import load_settings

NOT_BUILT_YET = "not built yet"


class CollectionNotBuiltError(LookupError):
    """Raised when a collection other than the v1 one is requested."""


def _check_known(name: str | None) -> str:
    settings = load_settings()
    wanted = name or settings.collection
    if wanted != settings.collection:
        raise CollectionNotBuiltError(f"collection '{wanted}' {NOT_BUILT_YET}")
    return wanted


def _client(path: str | None = None) -> chromadb.PersistentClient:
    settings = load_settings()
    return chromadb.PersistentClient(path=path or settings.chroma_dir)


def get_collection(name: str | None = None, path: str | None = None):
    """Get (creating) the known collection; reject unknown names."""
    wanted = _check_known(name)
    client = _client(path)
    return client.get_or_create_collection(wanted, metadata={"hnsw:space": "cosine"})


def upsert_chunks(
    chunks: list,
    vectors: list[list[float]],
    collection_name: str | None = None,
    path: str | None = None,
) -> int:
    """Idempotent upsert of parallel chunks/vectors; returns count written."""
    collection = get_collection(collection_name, path)
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        embeddings=vectors,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "volume": c.volume,
                "work": c.work,
                "chapter": c.chapter,
                "spine_index": c.spine_index,
                "kind": c.kind,
            }
            for c in chunks
        ],
    )
    return len(chunks)


def build_where(search_filter: dict | None) -> dict | None:
    """Map `{volume, work}` filter to a Chroma `where` clause (None = no filter)."""
    if not search_filter:
        return None
    clauses = []
    if search_filter.get("volume") is not None:
        clauses.append({"volume": int(search_filter["volume"])})
    if search_filter.get("work"):
        clauses.append({"work": search_filter["work"]})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def query_store(
    vector: list[float],
    top_k: int = 4,
    search_filter: dict | None = None,
    collection_name: str | None = None,
    path: str | None = None,
) -> list[dict]:
    """Nearest chunks by cosine similarity, score desc (score = 1 - distance)."""
    collection = get_collection(collection_name, path)
    result = collection.query(
        query_embeddings=[vector],
        n_results=max(top_k, 1),
        where=build_where(search_filter),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc_id, text, meta, dist in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        hits.append(
            {
                "chunk_id": doc_id,
                "text": text,
                "score": 1.0 - float(dist),
                "volume": meta.get("volume"),
                "work": meta.get("work", ""),
                "chapter": meta.get("chapter", ""),
            }
        )
    return hits


def collection_count(collection_name: str | None = None, path: str | None = None) -> int:
    return get_collection(collection_name, path).count()


def volume_breakdown(collection_name: str | None = None, path: str | None = None) -> dict[int, int]:
    """Per-volume chunk counts (one `get`; fine at v1 scale)."""
    collection = get_collection(collection_name, path)
    total = collection.count()
    if total == 0:
        return {}
    got = collection.get(include=["metadatas"], limit=total)
    breakdown: dict[int, int] = {}
    for meta in got["metadatas"]:
        volume = meta.get("volume")
        breakdown[volume] = breakdown.get(volume, 0) + 1
    return dict(sorted(breakdown.items()))


def reset_collection(collection_name: str | None = None, path: str | None = None) -> None:
    """Drop the known collection (danger-guarded by the index CLI)."""
    wanted = _check_known(collection_name)
    _client(path).delete_collection(wanted)
