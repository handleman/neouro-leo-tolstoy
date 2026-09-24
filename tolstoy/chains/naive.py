"""Naive stuff-everything chain (0009 step 2).

Embed question (same multilingual model) -> retrieve top-k (default 4,
no filter, no threshold) -> build prompt -> generate -> attach sources
in retrieval order. Empty retrieval answers "nothing found" with no
fake citations. Prompt builder lives here for v1; extracted to a shared
helper when Phase 4 adds variants.
"""

from tolstoy.config import load_settings

SYSTEM_RU = (
    "Отвечай по-русски голосом Толстого, опираясь только на приведённые "
    "отрывки. Указывай том/произведение/главу, когда это уместно."
)
SYSTEM_EN = (
    "Answer in English as a translation of the cited Russian passages, "
    "grounded only in the excerpts below. Say that the answer is translated "
    "from Russian sources."
)
REFUSAL_RU = "Не нашёл ответа на этот вопрос в моих произведениях."
REFUSAL_EN = "I found nothing on this question in my works."


def _embed(text: str) -> list[float]:
    from tolstoy.store import embed

    return embed.embed_query(text)


def _search(vector: list[float], top_k: int, collection: str) -> list[dict]:
    from tolstoy.store import chroma

    return chroma.query_store(vector, top_k=top_k, search_filter=None, collection_name=collection)


def _generate(system: str, user: str) -> str:
    from tolstoy.generate import ollama

    return ollama.generate(system, user)


def build_prompt(question: str, lang: str, hits: list[dict], budget: int) -> tuple[str, str]:
    """Return (system, user). Context chunks stuffed in order, truncated to budget."""
    system = SYSTEM_EN if lang == "en" else SYSTEM_RU
    parts: list[str] = []
    used = 0
    for rank, hit in enumerate(hits, 1):
        header = f"[{rank}] том {hit.get('volume')} | {hit.get('work')} | {hit.get('chapter')}"
        text = str(hit.get("text", ""))
        block = f"{header}\n{text}"
        room = budget - used
        if room <= 0:
            break
        if len(block) > room:
            block = block[:room]
        parts.append(block)
        used += len(block)
    context = "\n\n".join(parts)
    user = (
        f"Отрывки:\n{context}\n\nВопрос: {question}"
        if lang != "en"
        else (f"Excerpts (Russian originals):\n{context}\n\nQuestion: {question}")
    )
    return system, user


class NaiveChain:
    name = "naive"

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
        if not hits:
            return {
                "answer": REFUSAL_EN if lang == "en" else REFUSAL_RU,
                "sources": [],
                "answer_lang": lang,
            }
        system, user = build_prompt(question, lang, hits, self._budget)
        answer = self._generate(system, user)
        return {"answer": answer, "sources": sources, "answer_lang": lang}
