"""Chain interface (0009 step 2).

`Chain` = `name` + `ask(question, lang) -> {answer, sources, answer_lang}`.
Concrete chains live in sibling modules; the registry grows in Phases 4-5.
Dicts (not pydantic) keep chains importable without FastAPI.
"""

from typing import Protocol


class Chain(Protocol):
    name: str

    def ask(self, question: str, lang: str = "ru") -> dict:
        """Answer a question; `sources` = [{chunk_id, volume, work, chapter, score}]."""
        ...
