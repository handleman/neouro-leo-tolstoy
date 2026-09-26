"""Multi-query chain (0011 step 3).

Generator rewrites the question into N variants (default 3; RU variants for
`lang=ru`, English variants stay English for `lang=en` — cross-lingual
embeddings handle the match, no query translation in v1), retrieves top-k
per variant, merges with Reciprocal Rank Fusion (constant 60), dedupes by
`chunk_id`, keeps top-`final` (default `TOLSTOY_TOP_K`), then stuff ->
generate with the `naive` template voice.
"""

from __future__ import annotations

from tolstoy.chains.base import _embed, _generate, _search
from tolstoy.chains.prompts import render_prompt
from tolstoy.config import load_settings


def rrf_merge(rankings: list[list[dict]], k: int = 60, final_k: int = 4) -> list[dict]:
    """Reciprocal Rank Fusion over per-variant rankings (deterministic).

    Score(chunk) = sum over rankings of 1/(k + rank). Dedupe by `chunk_id`
    (first-seen dict wins); ties broken by chunk_id for determinism.
    """
    fused: dict[str, float] = {}
    seen: dict[str, dict] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, 1):
            cid = str(hit.get("chunk_id", ""))
            if not cid:
                continue
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in seen:
                seen[cid] = hit
    ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))
    return [dict(seen[cid]) for cid, _ in ordered[:final_k]]


def default_rewriter(question: str, lang: str, n: int) -> list[str]:
    """Ask the generator for N query variants (one per line); fall back to [question]."""
    from tolstoy.generate import ollama

    if lang == "ru":
        system = (
            "Перепиши вопрос тремя разными способами для поиска по произведениям "
            "Толстого. Ответь только вариантами, по одному на строку, без нумерации."
        )
    else:
        system = (
            "Rewrite the question in 3 different ways for search over Tolstoy's works. "
            "Reply with only the variants, one per line, no numbering."
        )
    try:
        raw = ollama.generate(system, question)
    except Exception:
        return [question]
    variants = [line.strip(" -0123456789.)\t") for line in raw.splitlines()]
    variants = [line for line in variants if line]
    return variants[:n] or [question]


class MultiQueryChain:
    """Rewrite -> retrieve per variant -> RRF -> naive-template generate."""

    name = "multi-query"
    template = "naive"
    gate_threshold = 0.0

    def __init__(
        self,
        embed_fn=_embed,
        search_fn=_search,
        generate_fn=_generate,
        rewrite_fn=None,
        variants: int | None = None,
        per_variant_k: int | None = None,
        final_k: int | None = None,
        rrf_constant: int | None = None,
        collection: str | None = None,
    ) -> None:
        settings = load_settings()
        self._embed = embed_fn
        self._search = search_fn
        self._generate = generate_fn
        variants_n = settings.multiquery_variants if variants is None else variants
        self._rewrite = rewrite_fn or (lambda q, lang: default_rewriter(q, lang, variants_n))
        self._variants = variants_n
        self._per_k = settings.multiquery_k if per_variant_k is None else per_variant_k
        self._final_k = settings.top_k if final_k is None else final_k
        self._rrf = settings.rrf_k if rrf_constant is None else rrf_constant
        self._collection = settings.collection if collection is None else collection
        self._budget = settings.chat_context_chars

    def ask(self, question: str, lang: str = "ru") -> dict:
        lang = lang if lang in ("ru", "en") else "ru"
        variants = list(self._rewrite(question, lang)[: self._variants]) or [question]
        rankings: list[list[dict]] = []
        for variant in variants:
            vector = self._embed(variant)
            rankings.append(self._search(vector, self._per_k, self._collection))
        top_hits = rrf_merge(rankings, k=self._rrf, final_k=self._final_k)
        if not top_hits:
            system, user = render_prompt(self.template, lang, question, [], self._budget)
            return {
                "answer": self._generate(system, user),
                "sources": [],
                "answer_lang": lang,
            }
        system, user = render_prompt(self.template, lang, question, top_hits, self._budget)
        answer = self._generate(system, user)
        sources = [
            {
                "chunk_id": hit["chunk_id"],
                "volume": hit.get("volume"),
                "work": hit.get("work", ""),
                "chapter": hit.get("chapter", ""),
                "score": hit.get("score", 0.0),
            }
            for hit in top_hits
        ]
        return {"answer": answer, "sources": sources, "answer_lang": lang}
