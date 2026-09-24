# Progress status (living dashboard)

> Single source of truth for "which phase are we on". Updated by the
> agent on every phase start/complete (rule in `AGENTS.md`). Every claim
> below must match verifiable repo state — commit, file, or command
> output. Narratives live in `notebooks/phase-N-journal.md`; plans live
> in `docs/design-docs/`; this file stays bullets.

- Last updated: 2026-09-24. Current: **Phase 4 complete → next: Phase 5 quality + eval**.

## Phases

- **Phase 0 — Dev environment: DONE** (commit `745f9b1`; journal `notebooks/phase-0-journal.md`; plan `docs/design-docs/0006-phase-0-dev-environment.md`). Evidence: `GET /health` skeleton, venv + Node workspace, Ollama + embed model smoke-tested.
- **Phase 1 — Corpus ingest: DONE** (commit `032ac7a`; journal `notebooks/phase-1-journal.md`; plan `docs/design-docs/0007-phase-1-corpus-ingest.md`). Evidence: `data/manifest.json` committed (22 vols, ~2.43M work words), `data/clean/vol01–22.json` rebuildable.
- **Phase 2 — Baseline retrieval: DONE** (commit `028d67f`, pushed; journal `notebooks/phase-2-journal.md`; plan `docs/design-docs/0008-phase-2-baseline-retrieval.md`). Evidence: 26,188 chunks in local `.chroma/` (`tolstoy-ru`), `POST /search` + REPL live, 38 tests green, RU/EN seed queries retrieve the same RU chunks.
- **Phase 3 — Naive chat: DONE** (journal `notebooks/phase-3-journal.md`; plan `docs/design-docs/0009-phase-3-naive-chat.md`; transcripts `evals/reports/phase-3-transcripts.md`). Evidence: `POST /chat` + Node REPL live (RU + translated EN with RU citations), 52 tests green, `ruff` + Node `typecheck` clean, 422/404/503 paths demonstrated live.
- **Phase 4 — Chains zoo + persona: DONE** (journal `notebooks/phase-4-journal.md`; plan `docs/design-docs/0010-phase-4-chains-zoo.md`; bank `evals/question_bank.json`; report `evals/reports/phase-4-comparison.md`). Evidence: 3 chains × 10 Q × 2 langs with author notes, 57 tests green, `ruff` clean, persona/cite-or-refuse + RU/EN refusals verified live via CLI.
- **Phase 5 — Quality (rerank, multi-query): NEXT** (plan `0011`). Exit: measured hit-rate per chain on ~20 Q/A bilingual eval set.
- **Phase 5 — Quality (rerank, multi-query): PLANNED** (plan `0011`). Exit: measured hit-rate per chain on ~20 Q/A bilingual eval set.
- **Phase 6 — Share & extend: PLANNED** (plan `0012`). Exit: README demo + lessons-learned note; optional `tolstoy-en` corpus only here.
