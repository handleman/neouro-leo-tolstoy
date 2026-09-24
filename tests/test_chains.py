"""Naive chain tests (0009): stubbed retriever + generator, no Ollama."""

from tolstoy.chains import CHAIN_REGISTRY
from tolstoy.chains.naive import SYSTEM_EN, SYSTEM_RU, NaiveChain, build_prompt

_HITS = [
    {
        "chunk_id": "ru-vol12-war-1-0",
        "text": "Смерть Ивана Ильича...",
        "score": 0.77,
        "volume": 12,
        "work": "Смерть Ивана Ильича",
        "chapter": "I",
    },
    {
        "chunk_id": "ru-vol12-war-2-0",
        "text": "Князь Андрей...",
        "score": 0.71,
        "volume": 12,
        "work": "Смерть Ивана Ильича",
        "chapter": "II",
    },
]


def _make_chain(captured: dict, hits: list[dict] | None = None) -> NaiveChain:
    stub_hits = hits if hits is not None else [dict(hit) for hit in _HITS]

    def fake_generate(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "сгенерированный ответ"

    return NaiveChain(
        embed_fn=lambda text: [0.1, 0.2, 0.3],
        search_fn=lambda vector, top_k, collection: stub_hits[:top_k],
        generate_fn=fake_generate,
    )


def test_registry_holds_naive() -> None:
    assert CHAIN_REGISTRY["naive"] is NaiveChain


def test_ask_attaches_sources_in_order() -> None:
    captured: dict = {}
    result = _make_chain(captured).ask("Что такое смерть?", "ru")
    assert result["answer"] == "сгенерированный ответ"
    assert result["answer_lang"] == "ru"
    assert [source["chunk_id"] for source in result["sources"]] == [
        "ru-vol12-war-1-0",
        "ru-vol12-war-2-0",
    ]
    assert result["sources"][0]["score"] >= result["sources"][1]["score"]
    assert captured["system"] == SYSTEM_RU
    assert "Смерть Ивана Ильича" in captured["user"]


def test_ask_en_requests_translation() -> None:
    captured: dict = {}
    result = _make_chain(captured).ask("What is death?", "en")
    assert result["answer_lang"] == "en"
    assert captured["system"] == SYSTEM_EN
    assert "translation" in captured["system"].lower()


def test_ask_empty_retrieval_refuses_without_citations() -> None:
    captured: dict = {}
    calls: list = []

    def fail_generate(system: str, user: str) -> str:
        calls.append((system, user))
        raise AssertionError("generator must not run on empty retrieval")

    chain = NaiveChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: [],
        generate_fn=fail_generate,
    )
    result = chain.ask("абракадабра несуществующая?", "ru")
    assert result["sources"] == []
    assert "Не нашёл" in result["answer"]
    assert calls == []
    assert captured == {}


def test_ask_empty_retrieval_en_refusal() -> None:
    def fail_generate(system: str, user: str) -> str:
        raise AssertionError("generator must not run on empty retrieval")

    chain = NaiveChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: [],
        generate_fn=fail_generate,
    )
    result = chain.ask("gibberish xyz?", "en")
    assert result["sources"] == []
    assert result["answer_lang"] == "en"
    assert "nothing" in result["answer"].lower()


def test_build_prompt_truncates_to_budget() -> None:
    system, user = build_prompt("вопрос?", "ru", [dict(hit) for hit in _HITS], budget=50)
    assert system == SYSTEM_RU
    assert len(user) <= 50 + len("Отрывки:\n\n\nВопрос: вопрос?")
