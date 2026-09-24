"""Chain comparison runner (0010 step 4).

Runs every chain x every bank question x both languages in-process
(real store + real Ollama generator) and writes
`evals/reports/phase-4-comparison.md`: per-question answers side by side
with sources, plus author-notes slots on style vs faithfulness filled in
after reading. Deterministic order: bank order, naive/persona/cite-or-refuse,
ru/en. A failed generation records an ERROR cell instead of aborting.
"""

import argparse
import datetime
import json
from pathlib import Path

from tolstoy.chains import CHAIN_REGISTRY
from tolstoy.config import load_settings

CHAIN_ORDER = ["naive", "persona", "cite-or-refuse"]
LANG_ORDER = ["ru", "en"]
REPO_ROOT = Path(__file__).resolve().parent.parent
BANK_PATH = REPO_ROOT / "evals" / "question_bank.json"
DEFAULT_OUT = REPO_ROOT / "evals" / "reports" / "phase-4-comparison.md"


def load_bank() -> list[dict]:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))["questions"]


def run_cell(chain_name: str, text: str, lang: str) -> dict:
    from tolstoy.generate.ollama import GeneratorUnavailable

    chain = CHAIN_REGISTRY[chain_name]()
    try:
        return chain.ask(text, lang)
    except GeneratorUnavailable as exc:
        return {"answer": f"ERROR: {exc}", "sources": [], "answer_lang": lang}


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return "(no sources)"
    lines = []
    for i, source in enumerate(sources, 1):
        lines.append(
            f"[{i}] vol{source['volume']:02d} | {source['work']} | "
            f"{source['chapter']} | {source['chunk_id']} | {source['score']:.4f}"
        )
    return "\n".join(lines)


def run_comparison(questions: list[dict], chains: list[str], langs: list[str], out: Path) -> Path:
    settings = load_settings()
    results: dict[tuple[str, str, str], dict] = {}
    total = len(questions) * len(chains) * len(langs)
    done = 0
    for item in questions:
        for chain_name in chains:
            for lang in langs:
                done += 1
                print(f"[{done}/{total}] {chain_name} {item['id']} {lang}", flush=True)
                results[(item["id"], chain_name, lang)] = run_cell(chain_name, item[lang], lang)

    stamp = datetime.date.today().isoformat()
    lines = [
        "# Phase 4 comparison — 3 chains x 10 questions x 2 langs",
        "",
        f"Date: {stamp}. Generator: `{settings.ollama_model}` "
        f"(temperature {settings.temperature}). Retrieval: top-{settings.top_k} "
        f"from `{settings.collection}`, context budget {settings.chat_context_chars} chars. "
        f"Refusal threshold (`cite-or-refuse` only): {settings.score_threshold}.",
        "",
    ]
    for item in questions:
        expected = item["expected"]
        lines += [
            f"## {item['id']}: {item['ru']}",
            "",
            f"EN: *{item['en']}*",
            "",
            f"Expected: vol{expected['volume']:02d} | {expected['work']}",
            "",
        ]
        for chain_name in chains:
            lines.append(f"### {chain_name}")
            lines.append("")
            for lang in langs:
                cell = results[(item["id"], chain_name, lang)]
                lines += [
                    f"**{lang}** (answer_lang={cell['answer_lang']}):",
                    "",
                    cell["answer"],
                    "",
                    "Sources:",
                    "```",
                    format_sources(cell["sources"]),
                    "```",
                    "",
                ]
        lines += [
            "**Author notes** (style vs faithfulness, EN fidelity vs RU sources):",
            "",
            "_TBD after reading._",
            "",
            "---",
            "",
        ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare chains on the question bank.")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--chains", default=",".join(CHAIN_ORDER))
    parser.add_argument("--questions", default="")
    parser.add_argument("--langs", default=",".join(LANG_ORDER))
    args = parser.parse_args(argv)
    bank = load_bank()
    if args.questions:
        wanted = set(args.questions.split(","))
        bank = [item for item in bank if item["id"] in wanted]
    run_comparison(
        bank,
        [c for c in args.chains.split(",") if c in CHAIN_REGISTRY],
        [lang for lang in args.langs.split(",") if lang in LANG_ORDER],
        Path(args.out),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
