"""Chain tests (0009 naive, 0010 zoo): stubbed retriever + generator, no Ollama."""

from tolstoy.chains import CHAIN_REGISTRY
from tolstoy.chains.cite_or_refuse import CiteOrRefuseChain
from tolstoy.chains.naive import NaiveChain
from tolstoy.chains.persona import PersonaChain
from tolstoy.chains.prompts import list_templates, load_template, render_prompt

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


def _stub_chain(cls, captured: dict, hits: list[dict] | None = None, **kwargs):
    stub_hits = hits if hits is not None else [dict(hit) for hit in _HITS]

    def fake_generate(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "сгенерированный ответ"

    return cls(
        embed_fn=lambda text: [0.1, 0.2, 0.3],
        search_fn=lambda vector, top_k, collection: stub_hits[:top_k],
        generate_fn=fake_generate,
        **kwargs,
    )


def test_registry_contains_exactly_three_chains() -> None:
    assert set(CHAIN_REGISTRY) == {"naive", "persona", "cite-or-refuse"}
    assert CHAIN_REGISTRY["naive"] is NaiveChain
    assert CHAIN_REGISTRY["persona"] is PersonaChain
    assert CHAIN_REGISTRY["cite-or-refuse"] is CiteOrRefuseChain


def test_all_templates_render_for_both_langs() -> None:
    pairs = list_templates()
    assert {(c, lang) for c, lang in pairs} == {
        ("naive", "ru"),
        ("naive", "en"),
        ("persona", "ru"),
        ("persona", "en"),
        ("cite-or-refuse", "ru"),
        ("cite-or-refuse", "en"),
    }
    for chain, lang in pairs:
        system, user = render_prompt(
            chain, lang, "вопрос?", [dict(hit) for hit in _HITS], budget=6000
        )
        assert system.strip()
        assert "{context}" not in user and "{question}" not in user
        assert "вопрос?" in user


def test_naive_ask_attaches_sources_in_order() -> None:
    captured: dict = {}
    result = _stub_chain(NaiveChain, captured).ask("Что такое смерть?", "ru")
    assert result["answer"] == "сгенерированный ответ"
    assert result["answer_lang"] == "ru"
    assert [source["chunk_id"] for source in result["sources"]] == [
        "ru-vol12-war-1-0",
        "ru-vol12-war-2-0",
    ]
    assert result["sources"][0]["score"] >= result["sources"][1]["score"]
    assert captured["system"] == load_template("naive", "ru")["system"]
    assert "Смерть Ивана Ильича" in captured["user"]


def test_naive_ask_en_requests_translation() -> None:
    captured: dict = {}
    result = _stub_chain(NaiveChain, captured).ask("What is death?", "en")
    assert result["answer_lang"] == "en"
    assert captured["system"] == load_template("naive", "en")["system"]
    assert "translation" in captured["system"].lower()


def test_persona_uses_voice_templates() -> None:
    captured_ru: dict = {}
    _stub_chain(PersonaChain, captured_ru).ask("Что такое смерть?", "ru")
    assert captured_ru["system"] == load_template("persona", "ru")["system"]
    assert "Толстой" in captured_ru["system"]
    assert "первого лица" in captured_ru["system"]
    assert "Отрывки" not in captured_ru["system"]  # voice lives in system, context in user

    captured_en: dict = {}
    result = _stub_chain(PersonaChain, captured_en).ask("What is death?", "en")
    assert result["answer_lang"] == "en"
    assert captured_en["system"] == load_template("persona", "en")["system"]
    assert "Tolstoy" in captured_en["system"]
    assert "first person" in captured_en["system"]


def test_cite_or_refuse_answers_above_threshold(monkeypatch) -> None:
    monkeypatch.setenv("TOLSTOY_SCORE_THRESHOLD", "0.55")
    captured: dict = {}
    result = _stub_chain(CiteOrRefuseChain, captured).ask("Что такое смерть?", "ru")
    assert result["answer"] == "сгенерированный ответ"
    assert len(result["sources"]) == 2
    assert captured["system"] == load_template("cite-or-refuse", "ru")["system"]
    assert "двумя-тремя" in captured["system"]


def test_cite_or_refuse_refuses_below_threshold(monkeypatch) -> None:
    monkeypatch.setenv("TOLSTOY_SCORE_THRESHOLD", "0.55")
    captured: dict = {}
    calls: list = []

    def fail_generate(system: str, user: str) -> str:
        calls.append((system, user))
        raise AssertionError("generator must not run below threshold")

    low_hits = [dict(_HITS[0], score=0.49), dict(_HITS[1], score=0.38)]
    chain = CiteOrRefuseChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: low_hits[:top_k],
        generate_fn=fail_generate,
    )
    result = chain.ask("абракадабра?", "ru")
    assert result["sources"] == []
    assert "Не нашёл" in result["answer"]
    assert calls == []
    assert captured == {}


def test_cite_or_refuse_refuses_en(monkeypatch) -> None:
    monkeypatch.setenv("TOLSTOY_SCORE_THRESHOLD", "0.55")

    def fail_generate(system: str, user: str) -> str:
        raise AssertionError("generator must not run below threshold")

    chain = CiteOrRefuseChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: [],
        generate_fn=fail_generate,
    )
    result = chain.ask("gibberish xyz?", "en")
    assert result["sources"] == []
    assert result["answer_lang"] == "en"
    assert "nothing" in result["answer"].lower()


def test_render_prompt_truncates_to_budget() -> None:
    system, user = render_prompt("naive", "ru", "вопрос?", [dict(h) for h in _HITS], 50)
    assert system == load_template("naive", "ru")["system"]
    assert len(user) <= 50 + len("Отрывки:\n\n\nВопрос: вопрос?")
