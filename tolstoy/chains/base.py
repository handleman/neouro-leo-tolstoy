"""Chain interface + shared stuff-everything flow (0009 step 2, 0010 step 2).

`Chain` = `name` + `ask(question, lang) -> {answer, sources, answer_lang}`.
`StuffChain` implements the shared flow (embed -> retrieve top-k ->
threshold gate -> render -> generate -> attach sources); concrete chains
differ only by template (`name`) and score gate (`threshold`).
Dicts (not pydantic) keep chains importable without FastAPI.
"""

from typing import Protocol

from tolstoy.chains.prompts import REFUSAL_EN, REFUSAL_RU, render_prompt
from tolstoy.config import load_settings


class Chain(Protocol):
    name: str

    def ask(self, question: str, lang: str = "ru") -> dict:
        """Answer a question; `sources` = [{chunk_id, volume, work, chapter, score}]."""
        ...


def _embed(text: str) -> list[float]:
    from tolstoy.store import embed

    return embed.embed_query(text)


def _search(vector: list[float], top_k: int, collection: str) -> list[dict]:
    from tolstoy.store import chroma

    return chroma.query_store(vector, top_k=top_k, search_filter=None, collection_name=collection)


def _generate(system: str, user: str) -> str:
    from tolstoy.generate import ollama

    return ollama.generate(system, user)


class StuffChain:
    """Shared flow; subclasses set `name` (template key) and `gate_threshold`."""

    name = "unset"
    gate_threshold = 0.0

    def __init__(
        self,
        embed_fn=_embed,
        search_fn=_search,
        generate_fn=_generate,
        top_k: int | None = None,
        collection: str | None = None,
    ) -> None:
        settings = load_settings()
        self._embed = embed_fn
        self._search = search_fn
        self._generate = generate_fn
        self._top_k = settings.top_k if top_k is None else top_k
        self._collection = settings.collection if collection is None else collection
        self._budget = settings.chat_context_chars

    def ask(self, question: str, lang: str = "ru") -> dict:
        lang = lang if lang in ("ru", "en") else "ru"
        vector = self._embed(question)
        hits = self._search(vector, self._top_k, self._collection)
        best = max((hit.get("score", 0.0) for hit in hits), default=0.0)
        if not hits or best < self.gate_threshold:
            return {
                "answer": REFUSAL_EN if lang == "en" else REFUSAL_RU,
                "sources": [],
                "answer_lang": lang,
            }
        system, user = render_prompt(self.name, lang, question, hits, self._budget)
        answer = self._generate(system, user)
        sources = [
            {
                "chunk_id": hit["chunk_id"],
                "volume": hit.get("volume"),
                "work": hit.get("work", ""),
                "chapter": hit.get("chapter", ""),
                "score": hit.get("score", 0.0),
            }
            for hit in hits
        ]
        return {"answer": answer, "sources": sources, "answer_lang": lang}
