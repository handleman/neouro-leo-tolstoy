# 0005: Implementation plan — overview and build order

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Conception, stack, and architecture are settled (0001–0004, `docs/` root). No code exists; `notebooks/` is empty; environment has Python 3.14, Node 24, and Ollama installed but not running. This doc is the master build order. Each phase gets its own exact step plan:

- 0006 — Phase 0, dev environment
- 0007 — Phase 1, corpus ingest (Russian-only EPUBs)
- 0008 — Phase 2, baseline retrieval (no LLM)
- 0009 — Phase 3, naive chat (first chain + Node CLI)
- 0010 — Phase 4, chains zoo (`persona`, `cite-or-refuse`)
- 0011 — Phase 5, quality (`rerank`, `multi-query`, eval harness)
- 0012 — Phase 6, share & extend (demo, transcripts, optional EN corpus)

Dependency order is strictly sequential 0 → 6: each phase's exit criteria are the next phase's entry assumptions. No phase starts until the previous one's exit checklist passes.

## Decision / Proposal

### Target repo layout (created incrementally, owned per phase)

```text
neouro-leo-tolstoy/
  pyproject.toml               # 0006: Python deps, ruff, pytest config
  .env.example                 # 0006: all tunable settings with defaults
  tolstoy/                     # Python package (Python owns all data/ML)
    __init__.py
    config.py                  # 0006: single env-driven settings source
    ingest/
      epub.py                  # 0007: OPF spine reader + XHTML extract
      clean.py                 # 0007: normalize + kind classification
      manifest.py              # 0007: manifest builder (CLI: python -m tolstoy.manifest)
      chunk.py                 # 0008: chunker
    store/
      embed.py                 # 0008: embedding-model loader
      chroma.py                # 0008: Store wrapper, collection tolstoy-ru
    chains/
      base.py                  # 0009: Chain interface + registry
      prompts/                 # 0010: versioned prompt templates, RU/EN per chain
      naive.py                 # 0009
      persona.py               # 0010
      cite_or_refuse.py        # 0010
      rerank.py                # 0011
      multiquery.py            # 0011
    generate/
      ollama.py                # 0009: Ollama client
    api/
      app.py                   # 0006 skeleton /health → 0008 +/search → 0009 +/chat
    eval/
      run.py score.py          # 0011: eval harness
    index.py search.py         # 0008: CLIs (index corpus, REPL search)
    clean.py manifest.py       # 0007: CLIs (thin wrappers over ingest/)
  web/                         # 0009: npm workspace (package.json, tsconfig, src/chat.ts)
  tests/                       # mirror per phase: test_config, test_epub, test_clean,
                               # test_manifest, test_chunk, test_store, test_api,
                               # test_chains, test_eval
  evals/
    question_bank.json         # 0010: 10 bilingual seeds → 0011: 20 with expected sources
    reports/                   # 0010+: comparison + eval reports (committed markdown)
  notebooks/                  # per-phase learning journal (phase-N-journal.md)
  data/
    manifest.json              # 0007: committed; sole versioned data artifact
    raw/ clean/                # gitignored (never committed)
  .chroma/ .venv/              # gitignored
```

### Shared conventions (all phases)

1. **Config** — every tunable (paths, model ids, ports, k, thresholds, chunk sizes) lives in `tolstoy/config.py`, read from env with the documented defaults; `.env.example` lists all vars. No hardcoded constants in logic modules.
2. **Determinism** — chunk IDs (`ru-vol{NN}-{work-slug}-{spine}-{ordinal}`), manifest SHAs, and upserts are deterministic; re-running any step on unchanged input is a no-op.
3. **Interfaces** — Python↔Node boundary is HTTP/JSON only (`/health`, `/search`, `/chat` per architecture.md). Chain interface is `ask(question, lang) → { answer, sources[], answer_lang }`.
4. **Testing** — each phase ships its `tests/test_*.py` plus exit-check commands listed in its plan; `pytest` + `ruff` gate every phase.
5. **Journals** — each phase ends with `notebooks/phase-N-journal.md` (what worked, failed, why) — the learning artifact is a deliverable, not an afterthought.

### Phase exits (summary; exact checklists in 0006–0012)

| Phase | Runnable result | Gate |
|---|---|---|
| 0 | skeleton repo, `/health` ok, models downloadable | 0006 checklist |
| 1 | `data/manifest.json` (22 vols) + `data/clean/` | 0007 checklist |
| 2 | `/search` + REPL over `tolstoy-ru`, RU+EN queries hit RU chunks | 0008 checklist |
| 3 | `/chat` + Node CLI, RU + translated EN sessions with citations | 0009 checklist |
| 4 | 3 chains × 10 bilingual questions, comparison report | 0010 checklist |
| 5 | rerank + multi-query + hit-rate table, winner documented | 0011 checklist |
| 6 | README demo, transcripts, lessons note, EN decision | 0012 checklist |

## Alternatives

- **One big-bang scaffold** — rejected: destroys the learning sequence; a failure in ingest would hide behind API/CLI code.
- **LangChain/LlamaIndex from Phase 2** — rejected per stack-decision: hand-rolled first so each RAG step stays visible; frameworks reconsidered only in Phase 6.
- **Monorepo split (separate Python/Node repos)** — rejected: single repo keeps manifest, evals, and transcripts next to the code that produced them.

## Consequences

- 0006–0012 become the build backlog in order; each names exact modules, contracts, tests, and exit commands.
- Layout decisions made here (package `tolstoy/`, `web/`, `evals/`, per-phase tests/journals) are binding unless a phase plan proposes an ADR to change them.
- v1 ships after Phase 3; Phases 4–5 are comparison/quality; Phase 6 shares.

## Open questions

1. Embedding model final id: default `paraphrase-multilingual-MiniLM-L12-v2` pending Phase 0 download + smoke test — confirm or replace in 0006 exit.
2. Ollama default: `llama3.2:1b` pending Phase 0 RU-fluency smoke test, candidate `qwen2.5:1.5b` — decided in 0006, consumed by 0009.
3. Do phase journals live as `notebooks/phase-N-journal.md` (proposed) or Jupyter `.ipynb`? Default markdown; `.ipynb` optional per phase.
