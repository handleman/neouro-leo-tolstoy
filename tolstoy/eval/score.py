"""Eval scorer (0011 step 1): pure functions, no store/generator imports.

Granularity: volume/work. A retrieval HIT = expected `work` appears in the
chain's top-k `sources[]` (matched on `work` string, not chunk_id — chunk ids
churn with re-chunking). `volume` is displayed for debugging; multi-volume
works (Anna Karenina vols 8-9, War and Peace vols 4-7) make strict
volume-matching a false-negative source, so work is the stable key.
"""

from __future__ import annotations


def _norm(work: object) -> str:
    return str(work or "").strip()


def is_hit(expected: dict, sources: list[dict], k: int = 4) -> bool:
    """True when expected work is in the first-k sources."""
    want = _norm(expected.get("work"))
    if not want:
        return False
    return any(_norm(source.get("work")) == want for source in (sources or [])[:k])


def en_ru_consistent(ru_sources: list[dict], en_sources: list[dict], k: int = 4) -> bool:
    """True when EN query retrieves ≥1 same RU work as its RU twin (top-k)."""
    ru_works = {_norm(source.get("work")) for source in (ru_sources or [])[:k]} - {""}
    en_works = {_norm(source.get("work")) for source in (en_sources or [])[:k]} - {""}
    return bool(ru_works & en_works)


def is_refusal(answer: str, sources: list[dict]) -> bool:
    """Refusal = empty sources + refusal marker (RU or EN template string)."""
    if sources:
        return False
    text = str(answer or "")
    return ("Не нашёл" in text) or ("nothing" in text.lower())


def summarize(cells: list[dict]) -> dict:
    """Aggregate cells into per-chain/per-lang hit-rate + EN->RU consistency.

    Each cell: {qid, chain, lang, hit: bool, error: str, latency: float}.
    Returns {"per_chain": {chain: {"ru": rate, "en": rate, "n": int}},
             "consistency": {chain: rate}, "overall": {chain: rate}}.
    """
    per_chain: dict[str, dict] = {}
    by_q: dict[tuple[str, str], dict[str, bool]] = {}
    for cell in cells:
        chain, lang, qid = cell["chain"], cell["lang"], cell["qid"]
        slot = per_chain.setdefault(chain, {"ru_hits": 0, "ru_n": 0, "en_hits": 0, "en_n": 0})
        if lang == "ru":
            slot["ru_n"] += 1
            slot["ru_hits"] += 1 if cell.get("hit") else 0
        elif lang == "en":
            slot["en_n"] += 1
            slot["en_hits"] += 1 if cell.get("hit") else 0
        by_q.setdefault((chain, qid), {})[lang] = bool(cell.get("hit"))
    table = {}
    for chain, slot in per_chain.items():
        table[chain] = {
            "ru": (slot["ru_hits"] / slot["ru_n"]) if slot["ru_n"] else 0.0,
            "en": (slot["en_hits"] / slot["en_n"]) if slot["en_n"] else 0.0,
            "n": slot["ru_n"],
        }
    overall = {}
    for chain, row in table.items():
        n_ru = per_chain[chain]["ru_n"]
        n_en = per_chain[chain]["en_n"]
        total_hits = per_chain[chain]["ru_hits"] + per_chain[chain]["en_hits"]
        overall[chain] = (total_hits / (n_ru + n_en)) if (n_ru + n_en) else 0.0
    return {"per_chain": table, "overall": overall}
