# neouro-leo-tolstoy

Self-educational RAG project: a vector database of Leo Tolstoy's works wired to a tiny talkative model, so you can chat with a "cyber Tolstoy" in his vocabulary.

> Status: v1 complete — all phases 0–6 done (5 chains measured, `rerank` wins at
> 0.55 hit-rate; demo transcripts + lessons note committed). Build followed
> `docs/design-docs/0005` → `0012` in order.

## What is this?

1. Build a clean, citable corpus of Tolstoy (open sources, public domain).
2. Index it into a local vector DB (chunk → embed → store).
3. Connect a small local LLM via Retrieval-Augmented Generation (RAG).
4. Experiment with **model chains** — different retrieve → rerank → prompt → generate pipelines — and compare them.

The point is learning RAG end-to-end, not serving production traffic.

## Docs

- [Vision](docs/vision.md) — why, what success looks like, example dialogues
- [Architecture](docs/architecture.md) — how RAG + chains fit together
- [Stack decision](docs/stack-decision.md) — Python + Node, Chroma, Ollama, why
- [Data sources](docs/data-sources.md) — which Tolstoy texts, where from, licensing
- [Roadmap](docs/roadmap.md) — phased learning plan, 0 → 6
- [Glossary](docs/glossary.md) — RAG terms in plain language

## Principle

Local-first, free, explainable. Every answer should cite the passages it came from. Every chain should be swappable and comparable.

## Next step

Read the docs in order above, then run the demo below. Full story:
design docs (`docs/design-docs/`), eval reports (`evals/reports/`), lessons
(`docs/design-docs/0013-lessons-learned.md`), live status
(`docs/progress/STATUS.md`).

## Demo (local-first RAG, RU-grounded answers in two languages)

Measured on the 20-question bilingual bank (Phase 5,
`evals/reports/phase-5-eval.md`): 5 chains × 20 Q × 2 langs, hit = expected
work in top-4 sources. Winner `rerank` — 0.55 overall (11/20 RU, 11/20 EN),
EN→RU consistency 0.90, ~4s/query on CPU. `naive`/`persona`/`cite-or-refuse`
0.47; `multi-query` 0.38 (RRF drift — complexity didn't pay).

RU session (`--lang ru --chain rerank`, verbatim, full text in
`evals/reports/demo-transcript-ru.md`):

```
> Что такое искусство?
Искусство – это архитектура, ваяние, живопись, музыка, поэзия во всех ее видах.
[1] vol15 | Что такое искусство? | II | ru-vol15-что-такое-искусство-10-3 | 0.8435
[2] vol15 | Что такое искусство? | V | ru-vol15-что-такое-искусство-13-0 | 0.7819
```

EN session — same question, same RU sources, translated answer
(`evals/reports/demo-transcript-en.md`):

```
> What is art?
[translated from RU sources]
Art is entertainment that gives people a break and relaxation. Art provides
enjoyment for those who are working hard […]
[1] vol15 | Незаконченное, наброски | О том, что называют искусством | ru-vol15-…-63-7 | 0.8081
[2] vol15 | Что такое искусство? | II | ru-vol15-что-такое-искусство-10-3 | 0.8332
```

Out-of-corpus gibberish is refused with no generator call (on the gated
`cite-or-refuse` chain; `rerank` has no gate by design):
`Не нашёл ответа на этот вопрос в моих произведениях.` / `(no sources)`.
Fluent off-topic (e.g. smartphones) can still pass the 0.55 score gate —
known limit, measured 3/6 probe refusals in Phase 5.

## Quickstart (fresh clone → chat, no corpus needed)

Prerequisites: Python 3.11+, Node 18+, GNU Make, Ollama running. The chat
runs on a prebuilt index downloaded from the
[index-tolstoy-ru-v1 release](https://github.com/handleman/neouro-leo-tolstoy/releases/tag/index-tolstoy-ru-v1)
(~215MB, SHA256-verified) — the 22-volume EPUB corpus is not required
(design: `docs/design-docs/0016-index-release.md`).

```bash
make setup     # venv, pip install, .env (never overwritten), Ollama model, npm install
make chat      # index: skip if populated, build if corpus present, else download release → API + chat REPL
```

Variants: `make chat CHAT_LANG=en`, `make chat CHAT_CHAIN=persona`,
`make reindex` (force rebuild), `make eval` (`EVAL_ARGS="--questions q01,q02"`
to slice), `make test` (pytest + ruff + typecheck), bare `make` lists
targets. Runner contract: `docs/design-docs/0015-local-runner.md`.

## Own tomes? Rebuild the index from your books

Don't have our 22 volumes (or have different ones)? Place any RU EPUBs in
`data/raw/` (layout: `docs/data-sources.md`) and run `make reindex` — it
requires the corpus (`check-corpus` gate) and rebuilds manifest → clean →
`.chroma/` from scratch (upserts are idempotent, safe to re-run). The eval
bank scores on work *names*, so a different edition still measures as long
as work titles match. To publish your rebuild for others, cut a new
`index-tolstoy-ru-vN` release (contract in `0016`) and point
`make fetch-index INDEX_TAG=index-tolstoy-ru-vN EXPECTED_CHUNKS=<n>` at it.

Under the hood (fallback if Make is unavailable — same commands the
targets wrap):

```bash
python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]" && cp -n .env.example .env
.venv/bin/python -m tolstoy.manifest build   # data/manifest.json
.venv/bin/python -m tolstoy.clean --all          # data/clean/ (regenerable)
.venv/bin/python -m tolstoy.index build --all # chunk → embed → .chroma/ (26,188 chunks)
.venv/bin/python -m uvicorn tolstoy.api.app:app --host 127.0.0.1 --port 8000 &
cd web && npm install && npm run chat -- --lang ru --chain rerank
```

Commands inside chat: `/ru` `/en` switch language, `/chain <name>` switch
chain (`naive|persona|cite-or-refuse|rerank|multi-query`), `/quit` leaves.
Checks: `.venv/bin/python -m pytest` (71 green), `ruff check tolstoy tests`,
`npm run typecheck --prefix web`. Quickstart path verified against a live
API + CLI on 2026-09-26 (transcripts above); corpus + index steps are the
same commands from Phases 0–2 journals.
