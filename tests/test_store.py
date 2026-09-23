"""Store tests: upsert idempotency, filters, unknown collection, ordering.

Uses an isolated Chroma dir per test (tmp_path) via TOLSTOY_CHROMA_DIR —
never touches the real `.chroma/`. Vectors are synthetic; the real
embedder is not loaded here.
"""

import pytest

from tolstoy.ingest.chunk import Chunk
from tolstoy.store import chroma
from tolstoy.store.chroma import CollectionNotBuiltError


def _chunk(chunk_id: str, text: str, volume: int, work: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        text=text,
        volume=volume,
        work=work,
        chapter="Глава",
        spine_index=1,
    )


@pytest.fixture
def isolated_store(monkeypatch, tmp_path):
    monkeypatch.setenv("TOLSTOY_CHROMA_DIR", str(tmp_path / "chroma"))
    return tmp_path


def test_upsert_twice_no_duplicates(isolated_store) -> None:
    chunks = [_chunk("ru-vol01-a-1-0", "текст один", 1, "Детство")]
    vectors = [[1.0, 0.0, 0.0]]
    chroma.upsert_chunks(chunks, vectors)
    chroma.upsert_chunks(chunks, vectors)
    assert chroma.collection_count() == 1


def test_filtered_query_respects_volume_and_work(isolated_store) -> None:
    chunks = [
        _chunk("ru-vol01-a-1-0", "детство текст", 1, "Детство"),
        _chunk("ru-vol08-b-2-0", "анна текст", 8, "Анна Каренина"),
    ]
    vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    chroma.upsert_chunks(chunks, vectors)

    vol_hits = chroma.query_store([1.0, 0.0, 0.0], top_k=5, search_filter={"volume": 8})
    assert [h["chunk_id"] for h in vol_hits] == ["ru-vol08-b-2-0"]

    work_hits = chroma.query_store([1.0, 0.0, 0.0], top_k=5, search_filter={"work": "Детство"})
    assert [h["chunk_id"] for h in work_hits] == ["ru-vol01-a-1-0"]


def test_unknown_collection_not_built_yet(isolated_store) -> None:
    with pytest.raises(CollectionNotBuiltError, match="not built yet"):
        chroma.collection_count(collection_name="tolstoy-en")
    with pytest.raises(CollectionNotBuiltError, match="not built yet"):
        chroma.query_store([1.0, 0.0, 0.0], collection_name="tolstoy-en")


def test_scores_ordered_desc(isolated_store) -> None:
    chunks = [
        _chunk("ru-vol01-a-1-0", "первый", 1, "Детство"),
        _chunk("ru-vol01-b-1-0", "второй", 1, "Детство"),
        _chunk("ru-vol01-c-1-0", "третий", 1, "Детство"),
    ]
    vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    chroma.upsert_chunks(chunks, vectors)
    hits = chroma.query_store([1.0, 0.0, 0.0], top_k=3)
    assert hits[0]["chunk_id"] == "ru-vol01-a-1-0"
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_build_where() -> None:
    assert chroma.build_where(None) is None
    assert chroma.build_where({}) is None
    assert chroma.build_where({"volume": 4}) == {"volume": 4}
    assert chroma.build_where({"volume": 4, "work": "X"}) == {
        "$and": [{"volume": 4}, {"work": "X"}]
    }
