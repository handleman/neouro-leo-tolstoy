"""Phase 5 tests (0011): scorer, RRF, rerank/multi-query stubs, runner structure."""

from pathlib import Path

from tolstoy.chains.multiquery import MultiQueryChain, rrf_merge
from tolstoy.chains.rerank import RerankChain
from tolstoy.eval.score import en_ru_consistent, is_hit, is_refusal

_HITS = [
    {"chunk_id": "c1", "text": "t1", "score": 0.9, "volume": 12, "work": "A", "chapter": "I"},
    {"chunk_id": "c2", "text": "t2", "score": 0.8, "volume": 12, "work": "B", "chapter": "II"},
    {"chunk_id": "c3", "text": "t3", "score": 0.7, "volume": 14, "work": "C", "chapter": "III"},
]


def _fake_generate(captured: dict):
    def fake(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "ответ"

    return fake


# --- scorer ---


def test_is_hit_on_work_match_miss_otherwise() -> None:
    assert is_hit({"volume": 12, "work": "B"}, _HITS, k=4) is True
    assert is_hit({"volume": 12, "work": "B"}, _HITS, k=1) is False
    assert is_hit({"volume": 99, "work": "ZZZ"}, _HITS, k=4) is False
    assert is_hit({"volume": 12, "work": ""}, _HITS, k=4) is False


def test_en_ru_consistent_matches_shared_work() -> None:
    ru = [dict(_HITS[0]), dict(_HITS[1])]
    en = [dict(_HITS[1]), dict(_HITS[2])]
    assert en_ru_consistent(ru, en, k=4) is True
    assert en_ru_consistent(ru, [dict(_HITS[2])], k=4) is False
    assert en_ru_consistent([], en, k=4) is False


def test_is_refusal_needs_empty_sources_plus_marker() -> None:
    assert is_refusal("Не нашёл ответа на этот вопрос в моих произведениях.", []) is True
    assert is_refusal("I found nothing on this question in my works.", []) is True
    assert is_refusal("Не нашёл ответа.", [{"chunk_id": "c1"}]) is False
    assert is_refusal("Полный ответ про Толстого.", []) is False


# --- RRF ---


def test_rrf_merge_dedupes_and_orders_deterministically() -> None:
    r1 = [dict(_HITS[0]), dict(_HITS[1])]
    r2 = [dict(_HITS[1]), dict(_HITS[0])]
    merged = rrf_merge([r1, r2], k=60, final_k=2)
    assert [hit["chunk_id"] for hit in merged] == ["c1", "c2"]  # tie -> chunk_id order
    merged1 = rrf_merge([[dict(_HITS[0])], [dict(_HITS[2])]], k=60, final_k=2)
    assert [hit["chunk_id"] for hit in merged1] == ["c1", "c3"]
    solo = rrf_merge([[dict(_HITS[2]), dict(_HITS[0])]], k=60, final_k=1)
    assert [hit["chunk_id"] for hit in solo] == ["c3"]
    dup = rrf_merge([[dict(_HITS[0])], [dict(_HITS[0])]], k=60, final_k=4)
    assert [hit["chunk_id"] for hit in dup] == ["c1"]


# --- new chains with stubs (no heavy models) ---


def test_rerank_rescores_broad_candidates() -> None:
    captured: dict = {}
    chain = RerankChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: [dict(h) for h in _HITS][:top_k],
        generate_fn=_fake_generate(captured),
        score_fn=lambda query, texts: [0.1, 0.9, 0.5],  # c2 wins
        broad_k=3,
        final_k=2,
    )
    result = chain.ask("вопрос?", "ru")
    assert result["answer"] == "ответ"
    assert [s["chunk_id"] for s in result["sources"]] == ["c2", "c3"]
    assert "вопрос?" in captured["user"]


def test_rerank_empty_candidates_still_generates() -> None:
    captured: dict = {}
    chain = RerankChain(
        embed_fn=lambda text: [0.1],
        search_fn=lambda vector, top_k, collection: [],
        generate_fn=_fake_generate(captured),
        score_fn=lambda query, texts: [],
    )
    result = chain.ask("вопрос?", "en")
    assert result["answer_lang"] == "en"
    assert result["sources"] == []


def test_multiquery_merges_variants_with_rrf() -> None:
    captured: dict = {}
    seen: list[str] = []

    def fake_search(vector, top_k, collection):
        query = seen[-1] if seen else ""
        if query == "v1":
            return [dict(_HITS[0]), dict(_HITS[1])][:top_k]
        return [dict(_HITS[1]), dict(_HITS[2])][:top_k]

    def fake_embed(text):
        seen.append(text)
        return [0.1]

    chain = MultiQueryChain(
        embed_fn=fake_embed,
        search_fn=fake_search,
        generate_fn=_fake_generate(captured),
        rewrite_fn=lambda q, lang: ["v1", "v2"],
        variants=2,
        per_variant_k=2,
        final_k=2,
    )
    result = chain.ask("вопрос?", "ru")
    assert result["answer"] == "ответ"
    # c2 appears in both variants -> top; then c1 vs c3 tie -> chunk_id order
    assert [s["chunk_id"] for s in result["sources"]] == ["c2", "c1"]
    assert seen == ["v1", "v2"]


# --- runner structure ---


def test_runner_report_covers_chains_questions_langs(tmp_path: Path, monkeypatch) -> None:
    import tolstoy.eval.run as run_mod

    bank = [
        {"id": "qA", "ru": "ru-a?", "en": "en-a?", "expected": {"volume": 12, "work": "A"}},
        {"id": "qB", "ru": "ru-b?", "en": "en-b?", "expected": {"volume": 12, "work": "B"}},
    ]

    class StubChain:
        def __init__(self, work: str):
            self._work = work

        def ask(self, question: str, lang: str = "ru") -> dict:
            return {
                "answer": f"ans {question} {lang}",
                "sources": [
                    {
                        "chunk_id": f"{self._work}-{lang}",
                        "volume": 12,
                        "work": self._work,
                        "chapter": "I",
                        "score": 0.9,
                    }
                ],
                "answer_lang": lang,
            }

    fake_registry = {"s1": lambda: StubChain("A"), "s2": lambda: StubChain("B")}
    monkeypatch.setattr(run_mod, "CHAIN_REGISTRY", fake_registry)
    out = tmp_path / "phase-5-eval.md"
    run_mod.run_eval(bank, ["s1", "s2"], ["ru", "en"], k=4, out=out)
    text = out.read_text(encoding="utf-8")
    assert "Hit-rate@k" in text
    for qid in ("qA", "qB"):
        assert qid in text
    for chain in ("s1", "s2"):
        assert chain in text
    assert "Refusal precision" in text
