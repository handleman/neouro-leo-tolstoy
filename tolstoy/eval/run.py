"""Eval runner (0011 step 1): all chains x bank questions x langs -> markdown.

Deterministic order: bank order, CHAIN_ORDER, LANG_ORDER. Each cell calls
`chain.ask(text, lang)` once (real store + real generator), times it, scores
retrieval hit-rate@k against `expected.work`, catches generation errors as
ERROR cells (hit=False, sources=[]). Refusal probes run on `cite-or-refuse`
only (secondary metric). Writes `evals/reports/phase-5-eval.md`.
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
from pathlib import Path

from tolstoy.chains import CHAIN_REGISTRY
from tolstoy.config import load_settings
from tolstoy.eval.score import en_ru_consistent, is_hit, is_refusal

CHAIN_ORDER = ["naive", "persona", "cite-or-refuse", "rerank", "multi-query"]
LANG_ORDER = ["ru", "en"]
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BANK_PATH = REPO_ROOT / "evals" / "question_bank.json"
PROBES_PATH = REPO_ROOT / "evals" / "refusal_probes.json"
DEFAULT_OUT = REPO_ROOT / "evals" / "reports" / "phase-5-eval.md"


def load_bank() -> list[dict]:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))["questions"]


def load_probes() -> list[dict]:
    return json.loads(PROBES_PATH.read_text(encoding="utf-8"))["probes"]


def run_cell(chain_name: str, text: str, lang: str) -> dict:
    chain = CHAIN_REGISTRY[chain_name]()
    started = time.perf_counter()
    try:
        result = chain.ask(text, lang)
        latency = time.perf_counter() - started
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "answer_lang": result.get("answer_lang", lang),
            "latency": latency,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 — ERROR cell, never abort the run
        return {
            "answer": f"ERROR: {exc}",
            "sources": [],
            "answer_lang": lang,
            "latency": time.perf_counter() - started,
            "error": str(exc),
        }


def run_eval(
    questions: list[dict],
    chains: list[str],
    langs: list[str],
    k: int,
    out: Path,
) -> Path:
    settings = load_settings()
    cells: dict[tuple[str, str, str], dict] = {}
    total = len(questions) * len(chains) * len(langs)
    done = 0
    for item in questions:
        for chain_name in chains:
            for lang in langs:
                done += 1
                print(f"[{done}/{total}] {chain_name} {item['id']} {lang}", flush=True)
                cell = run_cell(chain_name, item[lang], lang)
                cell["hit"] = is_hit(item["expected"], cell["sources"], k)
                cells[(item["id"], chain_name, lang)] = cell

    # Refusal probes on cite-or-refuse (secondary metric), both langs.
    probe_rows: list[dict] = []
    if "cite-or-refuse" in chains:
        for probe in load_probes():
            for lang in langs:
                cell = run_cell("cite-or-refuse", probe[lang], lang)
                probe_rows.append(
                    {
                        "id": probe["id"],
                        "lang": lang,
                        "refused": is_refusal(cell["answer"], cell["sources"]),
                        "answer": cell["answer"][:200],
                    }
                )

    stamp = datetime.date.today().isoformat()
    lines = [
        f"# Phase 5 eval — {len(chains)} chains x {len(questions)} questions x {len(langs)} langs",
        "",
        f"Date: {stamp}. Generator: `{settings.ollama_model}` "
        f"(temperature {settings.temperature}). Retrieval: top-{k} from "
        f"`{settings.collection}` (rerank broad-{settings.rerank_broad_k} "
        f"via `{settings.rerank_model}`, final-{settings.rerank_final_k}; "
        f"multi-query {settings.multiquery_variants}x{settings.multiquery_k} "
        f"RRF k={settings.rrf_k}). Scorer: hit = expected work in top-{k} "
        f"sources[]. EN->RU = EN top-{k} shares ≥1 work with RU twin.",
        "",
        "## Hit-rate@k per chain",
        "",
        "| chain | RU | EN | overall | EN->RU consistent | avg latency s |",
        "|---|---|---|---|---|---|",
    ]
    avgs: dict[str, float] = {}
    for chain_name in chains:
        for lang in langs:
            subset = [cells[(q["id"], chain_name, lang)] for q in questions]
            _ = subset  # clarity: rows computed below per chain
        ru_hits = sum(cells[(q["id"], chain_name, "ru")]["hit"] for q in questions if "ru" in langs)
        en_hits = sum(cells[(q["id"], chain_name, "en")]["hit"] for q in questions if "en" in langs)
        n_ru = len(questions) if "ru" in langs else 0
        n_en = len(questions) if "en" in langs else 0
        ru_rate = ru_hits / n_ru if n_ru else 0.0
        en_rate = en_hits / n_en if n_en else 0.0
        overall = (ru_hits + en_hits) / (n_ru + n_en) if (n_ru + n_en) else 0.0
        consistent = (
            sum(
                en_ru_consistent(
                    cells[(q["id"], chain_name, "ru")]["sources"],
                    cells[(q["id"], chain_name, "en")]["sources"],
                    k,
                )
                for q in questions
            )
            / len(questions)
            if ("ru" in langs and "en" in langs)
            else 0.0
        )
        lat = [cells[(q["id"], chain_name, lang)]["latency"] for q in questions for lang in langs]
        avg_lat = sum(lat) / len(lat) if lat else 0.0
        avgs[chain_name] = avg_lat
        lines.append(
            f"| {chain_name} | {ru_hits}/{n_ru} ({ru_rate:.2f}) | "
            f"{en_hits}/{n_en} ({en_rate:.2f}) | {overall:.2f} | "
            f"{consistent:.2f} | {avg_lat:.1f} |"
        )
    def _chain_hits(chain_name: str) -> int:
        return sum(cells[(q["id"], chain_name, lang)]["hit"] for q in questions for lang in langs)

    best = max(chains, key=_chain_hits) if chains else "-"
    lines += [
        "",
        f"**Retrieval winner (hit-rate): `{best}`.** Author judgment (complexity "
        "vs payoff, refusal behaviour, latency cost): _TBD after reading._",
        "",
        "## Refusal precision (`cite-or-refuse`, out-of-corpus probes)",
        "",
        "| probe | lang | refused | answer head |",
        "|---|---|---|---|",
    ]
    for row in probe_rows:
        head = row["answer"].replace("\n", " ").replace("|", "/")
        lines.append(f"| {row['id']} | {row['lang']} | {row['refused']} | {head} |")
    if not probe_rows:
        lines.append("| — | — | — | (cite-or-refuse not in --chains) |")
    refused_n = sum(1 for row in probe_rows if row["refused"])
    lines += [
        "",
        f"Refused {refused_n}/{len(probe_rows)} probe cells. "
        "In-corpus false-refusal check: see per-question tables "
        "(`cite-or-refuse` rows with `(no sources)` on q01-q20 = failure).",
        "",
        "## Per-question detail (retrieval verdict + sources head)",
        "",
    ]
    for item in questions:
        expected = item["expected"]
        lines += [
            f"### {item['id']}: {item['ru']}",
            "",
            f"EN: *{item['en']}*",
            "",
            f"Expected: vol{expected['volume']:02d} | {expected['work']}",
            "",
        ]
        for chain_name in chains:
            bits = []
            for lang in langs:
                cell = cells[(item["id"], chain_name, lang)]
                mark = "HIT" if cell["hit"] else "miss"
                err = f" ERROR={cell['error'][:80]}" if cell["error"] else ""
                works = ", ".join(
                    f"{s.get('work')} (v{s.get('volume')})" for s in cell["sources"][:k]
                ) or "(no sources)"
                bits.append(f"{lang}:{mark} {cell['latency']:.1f}s{err} [{works}]")
            lines += [f"- **{chain_name}**: " + " | ".join(bits), ""]
        lines += ["---", ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5 eval harness.")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--chains", default=",".join(CHAIN_ORDER))
    parser.add_argument("--langs", default=",".join(LANG_ORDER))
    parser.add_argument("--questions", default="")
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args(argv)
    bank = load_bank()
    if args.questions:
        wanted = set(args.questions.split(","))
        bank = [item for item in bank if item["id"] in wanted]
    run_eval(
        bank,
        [c for c in args.chains.split(",") if c in CHAIN_REGISTRY],
        [lang for lang in args.langs.split(",") if lang in LANG_ORDER],
        max(1, args.k),
        Path(args.out),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
