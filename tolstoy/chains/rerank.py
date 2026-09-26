"""Rerank chain (0011 step 2).

Broad retrieve top-`broad_k` (default 12) from `tolstoy-ru`, rescore each
candidate with a cross-encoder (default
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` — multilingual MiniLM, MMARCO
family, CPU-friendly, Russian-capable), keep top-`final_k` (default 4),
then the standard stuff -> generate path with the `naive` template voice
(retrieval is the experiment here, not persona).
"""

from __future__ import annotations

from tolstoy.chains.base import _embed, _generate, _search
from tolstoy.chains.prompts import render_prompt
from tolstoy.config import load_settings

_CROSS_ENCODER = None


def default_scorer(query: str, texts: list[str]) -> list[float]:
    """Score (query, text) pairs with the configured cross-encoder (lazy)."""
    global _CROSS_ENCODER
    if _CROSS_ENCODER is None:
        from sentence_transformers import CrossEncoder

        _CROSS_ENCODER = CrossEncoder(load_settings().rerank_model)
    batch = load_settings().rerank_batch
    pairs = [(query, text) for text in texts]
    scores = _CROSS_ENCODER.predict(pairs, batch_size=batch)
    return [float(score) for score in scores]


class RerankChain:
    """Broad-retrieve -> cross-encode -> top-final -> naive-template generate."""

    name = "rerank"
    template = "naive"
    gate_threshold = 0.0

    def __init__(
        self,
        embed_fn=_embed,
        search_fn=_search,
        generate_fn=_generate,
        score_fn=None,
        broad_k: int | None = None,
        final_k: int | None = None,
        collection: str | None = None,
    ) -> None:
        settings = load_settings()
        self._embed = embed_fn
        self._search = search_fn
        self._generate = generate_fn
        self._score = score_fn or default_scorer
        self._broad_k = settings.rerank_broad_k if broad_k is None else broad_k
        self._final_k = settings.rerank_final_k if final_k is None else final_k
        self._collection = settings.collection if collection is None else collection
        self._budget = settings.chat_context_chars

    def ask(self, question: str, lang: str = "ru") -> dict:
        lang = lang if lang in ("ru", "en") else "ru"
        vector = self._embed(question)
        candidates = self._search(vector, self._broad_k, self._collection)
        if not candidates:
            system, user = render_prompt(self.template, lang, question, [], self._budget)
            return {
                "answer": self._generate(system, user),
                "sources": [],
                "answer_lang": lang,
            }
        texts = [str(hit.get("text", "")) for hit in candidates]
        scores = list(self._score(question, texts))
        ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
        top_hits = [dict(hit) for hit, _ in ranked[: self._final_k]]
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
