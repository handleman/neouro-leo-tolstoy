"""Retrieval API tests: /health contract + POST /search (no model load).

The real embedder/store are monkeypatched out; store-behavior tests live
in test_store.py.
"""

from fastapi.testclient import TestClient

from tolstoy.api import app as app_module
from tolstoy.api.app import app

client = TestClient(app)

_HITS = [
    {
        "chunk_id": "ru-vol04-slug-6-0",
        "text": "Смерть Ивана Ильича...",
        "score": 0.81,
        "volume": 4,
        "work": "Война и мир",
        "chapter": "Часть первая",
    },
    {
        "chunk_id": "ru-vol04-slug-7-1",
        "text": "Князь Андрей...",
        "score": 0.77,
        "volume": 4,
        "work": "Война и мир",
        "chapter": "Часть первая",
    },
]


def _patch_retrieval(monkeypatch, captured: dict | None = None):
    monkeypatch.setattr(app_module, "embed_query_text", lambda text: [0.1, 0.2, 0.3])

    def fake_query(vector, top_k, search_filter, collection):
        if captured is not None:
            captured.update(
                {
                    "vector": vector,
                    "top_k": top_k,
                    "filter": search_filter,
                    "collection": collection,
                }
            )
        hits = [dict(hit) for hit in _HITS]
        if search_filter and search_filter.get("volume") == 8:
            hits = []  # fixture honors volume filtering
        return hits[:top_k]

    monkeypatch.setattr(app_module, "run_search_query", fake_query)


def test_health_returns_retrieval_contract(monkeypatch) -> None:
    import tolstoy.store.chroma as chroma_module

    monkeypatch.setattr(chroma_module, "collection_count", lambda *a, **k: 123)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "retrieval"
    assert body["collection"] == "tolstoy-ru"
    assert body["chunk_count"] == 123
    assert body["embed_model"] == "paraphrase-multilingual-MiniLM-L12-v2"


def test_search_happy_path(monkeypatch) -> None:
    _patch_retrieval(monkeypatch)
    response = client.post("/search", json={"query": "Что Толстой говорит о смерти?"})
    assert response.status_code == 200
    body = response.json()
    assert body["collection"] == "tolstoy-ru"
    assert [hit["chunk_id"] for hit in body["results"]] == [
        "ru-vol04-slug-6-0",
        "ru-vol04-slug-7-1",
    ]
    assert body["results"][0]["score"] >= body["results"][1]["score"]


def test_search_empty_query_is_422(monkeypatch) -> None:
    _patch_retrieval(monkeypatch)
    assert client.post("/search", json={"query": "   "}).status_code == 422
    assert client.post("/search", json={"query": ""}).status_code == 422


def test_search_unknown_collection_is_404(monkeypatch) -> None:
    _patch_retrieval(monkeypatch)
    response = client.post("/search", json={"query": "смерть", "collection": "tolstoy-en"})
    assert response.status_code == 404
    assert "not built yet" in response.json()["detail"]


def test_search_filter_forwarded(monkeypatch) -> None:
    captured: dict = {}
    _patch_retrieval(monkeypatch, captured)
    response = client.post(
        "/search",
        json={"query": "смерть", "top_k": 1, "filter": {"volume": 4}},
    )
    assert response.status_code == 200
    assert captured["filter"] == {"volume": 4}
    assert captured["top_k"] == 1
    assert len(response.json()["results"]) == 1


def test_search_top_k_clamped(monkeypatch) -> None:
    captured: dict = {}
    _patch_retrieval(monkeypatch, captured)
    client.post("/search", json={"query": "смерть", "top_k": 99})
    assert captured["top_k"] == 20


_CHAT_RESULT = {
    "answer": "Смерть есть пробуждение.",
    "sources": [
        {
            "chunk_id": "ru-vol12-war-1-0",
            "volume": 12,
            "work": "Смерть Ивана Ильича",
            "chapter": "I",
            "score": 0.77,
        }
    ],
    "answer_lang": "ru",
}


def _patch_chat(monkeypatch, result: dict | None = None, exc: Exception | None = None):
    def fake_ask(chain_name, question, lang, collection):
        if exc is not None:
            raise exc
        body = dict(result or _CHAT_RESULT)
        body["answer_lang"] = lang
        return body

    monkeypatch.setattr(app_module, "run_chat_ask", fake_ask)


def test_chat_happy_path(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    response = client.post("/chat", json={"question": "Что такое смерть?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Смерть есть пробуждение."
    assert body["answer_lang"] == "ru"
    assert body["chain"] == "naive"
    assert body["sources"][0]["chunk_id"] == "ru-vol12-war-1-0"


def test_chat_answer_lang_echo(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    response = client.post("/chat", json={"question": "What is death?", "lang": "en"})
    assert response.status_code == 200
    assert response.json()["answer_lang"] == "en"


def test_chat_empty_question_is_422(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    assert client.post("/chat", json={"question": "   "}).status_code == 422


def test_chat_bad_lang_is_422(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    assert client.post("/chat", json={"question": "смерть", "lang": "de"}).status_code == 422


def test_chat_unknown_chain_is_422(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    response = client.post("/chat", json={"question": "смерть", "chain": "nope"})
    assert response.status_code == 422
    assert "unknown chain" in response.json()["detail"]


def test_chat_unknown_collection_is_404(monkeypatch) -> None:
    _patch_chat(monkeypatch)
    response = client.post("/chat", json={"question": "смерть", "collection": "tolstoy-en"})
    assert response.status_code == 404
    assert "not built yet" in response.json()["detail"]


def test_chat_generator_down_is_503(monkeypatch) -> None:
    from tolstoy.generate.ollama import GeneratorUnavailable

    _patch_chat(monkeypatch, exc=GeneratorUnavailable("ollama down"))
    response = client.post("/chat", json={"question": "смерть"})
    assert response.status_code == 503


def test_health_reports_ollama(monkeypatch) -> None:
    import tolstoy.generate.ollama as ollama_module
    import tolstoy.store.chroma as chroma_module

    monkeypatch.setattr(chroma_module, "collection_count", lambda *a, **k: 26188)
    monkeypatch.setattr(ollama_module, "is_reachable", lambda: True)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ollama_model"] == "llama3.2:1b"
    assert body["ollama_reachable"] is True
