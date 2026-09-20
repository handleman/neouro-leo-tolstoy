# 0011: Phase 5 — quality: rerank, multi-query, eval harness (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 4 exit (3 comparable chains, 10-question bank, comparison report). Goal: two retrieval-focused chains plus a tiny eval harness that measures whether they actually help. Question the phase answers: when does extra complexity pay? Interfaces frozen; new chains join `CHAIN_REGISTRY` as `{ naive, persona, cite-or-refuse, rerank, multi-query }`.

## Decision / Proposal

Build in this exact order.

### Step 1 — Eval harness first `tolstoy/eval/run.py` + `score.py`

- Extend `evals/question_bank.json` to ~20 entries: `{ id, ru, en, expected: { volume, work }, notes }` (expected source at volume/work granularity — chunk-level pinning is overkill for v1).
- Primary metric — retrieval hit-rate@k: fraction of questions (per language) whose expected `volume/work` appears in the chain's `sources[]`. Reported per chain × per language, plus EN→RU recall column (EN question hitting the same RU work as its RU twin).
- Secondary metric — refusal precision for `cite-or-refuse`: 2–3 out-of-corpus probes (e.g. modern topics absent from Tolstoy) must refuse; in-corpus questions must not.
- Runner CLI `python -m tolstoy.evaluate --chains ... --lang ru,en --k 4` writes `evals/reports/phase-5-eval.md` (hit-rate table + winner + author judgment). Deterministic question order; generator calls logged with chain/lang/question ids for reproducibility.

### Step 2 — Rerank chain `tolstoy/chains/rerank.py`

- Retrieve top-12 from `tolstoy-ru` (config `TOLSTOY_RERANK_BROAD=12`), score each candidate with a cross-encoder (candidate: multilingual MiniLM cross-encoder from the MMARCO family — CPU-friendly, Russian-capable; exact id fixed at build time after a smoke test), keep top-4, then the standard stuff → generate path.
- Config: broad-k, final-k (= 4), rerank model id, CPU batch size. Document per-query latency cost in the journal (precision at a price — the learning point).

### Step 3 — Multi-query chain `tolstoy/chains/multiquery.py`

- Generator rewrites the question into 3 variants (RU for `lang=ru`; for `lang=en`, variants stay English — cross-lingual embeddings handle the match, no query translation in v1), retrieves top-4 per variant, merges with Reciprocal Rank Fusion (constant 60), dedupes by `chunk_id`, keeps top-4, then stuff → generate.
- Config: variant count (3), per-variant k, RRF constant. A query-translation pre-step is explicitly NOT included (candidate for a follow-up experiment, noted in the report).

### Step 4 — Run evals, document winner

- Run the harness over all 5 chains × 20 questions × 2 langs; commit `evals/reports/phase-5-eval.md` with the hit-rate table, latency notes, refusal-precision check, and a written winner verdict (which chain, why, when the extra cost is/isn't worth it).

### Tests (new/extend)

- `test_eval.py` — scorer unit tests (hit, miss, EN→RU match counting; refusal precision on fixture answers); runner structural test (report covers all chains × questions × langs).
- RRF merge unit test (deterministic ordering, `chunk_id` dedupe) with fixture rankings.
- Chain registration test extended to 5 chains; rerank/multi-query run green with stubbed generator + stubbed scorer/rewriter (no heavy models in tests).

### Exit checklist

1. `python -m tolstoy.evaluate` runs end to end; `evals/reports/phase-5-eval.md` committed with hit-rate per chain (incl. EN→RU recall) + documented winner.
2. Rerank latency cost measured and recorded (broad-12 + cross-encoder per-query time on CPU).
3. Refusal-precision probes behave (out-of-corpus refuses, in-corpus answers).
4. `pytest` + `ruff` green; `notebooks/phase-5-journal.md` written (recall vs precision, eval-design lessons, when complexity paid).

## Alternatives

- **LLM-as-reranker instead of cross-encoder** — rejected for v1: slower on CPU, costlier per query, harder to isolate (generator judging generator); cross-encoder is the honest precision-vs-cost experiment.
- **Chunk-level expected sources** — rejected: volume/work granularity is stable under re-chunking; chunk ids churn with tuning and would brittle the eval.
- **Dedicated MT model for EN query translation** — deferred (0003): generator-side handling plus multilingual embeddings already cover EN; revisit only if EN→RU recall disappoints here.

## Consequences

- The project gets its first measured claim ("chain X wins retrieval at cost Y") instead of vibes.
- Eval bank + harness become the regression suite for any future tuning (chunk sizes, thresholds, models).
- Phase 6 inherits a documented winner to demo and a loser-list to explain.

## Open questions

1. Cross-encoder exact id + CPU latency acceptability — measured at build time.
2. Hit-rate target (what counts as "good" for 1B-generator RAG on Tolstoy?) — set judgmentally in the report, not as a fake SLO.
3. Does multi-query need the query-translation pre-step after all? Decided from the EN→RU recall column.
