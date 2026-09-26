# Phase 5 journal — quality: rerank, multi-query, eval harness

Date: 2026-09-26. Plan: `docs/design-docs/0011-phase-5-quality-eval.md`.

## Result

Eval harness first (`tolstoy/eval/score.py + run.py`, `python -m tolstoy.evaluate`),
then two retrieval chains (`RerankChain`, `MultiQueryChain` + `rrf_merge`) into
`CHAIN_REGISTRY` (now 5). Bank 10→20 Q (q11–q20 grounded in manifest work_list)
+ `evals/refusal_probes.json` (3 out-of-corpus probes). Full run: 5 chains ×
20 Q × 2 langs = 200 cells, 0 ERRORs, report `evals/reports/phase-5-eval.md`
with filled winner verdict. `pytest` 71 passed, `ruff` clean.

Measured hit-rate@4 (work in top-4 sources): rerank 0.55 (11/20 RU, 11/20 EN)
wins; naive/persona/cite-or-refuse 0.47; multi-query 0.38. Avg latency:
cite 2.3s, naive 4.2s, rerank 4.3s, multi-query 6.8s, persona 8.7s.
EN→RU consistency: naive/persona 1.00, cite 0.95, rerank 0.90, multi-query
0.55. Refusal probes: 3/6 refuse; 0 false refusals on 40 in-corpus
cite-or-refuse cells.

## Recall vs precision

- Rerank is pure precision play and it worked: +1 RU / +2 EN hits over naive
  by reordering broad-12. It never adds recall outside the broad set — every
  rerank miss was also a broad-12 miss (e.g. q02 "Как он описывает смерть?"
  misses everywhere; the embedder buries Ivan Ilyich under О жизни/пеасants
  for pronoun phrasing, while Phase 2's "Что Толстой говорит о смерти?"
  retrieved it — wording sensitivity is real).
- Multi-query aimed at recall and lost it: RU 0.30 vs 0.50 naive. RRF over 3
  generator variants drifts off title-match anchors (q07 art, q11/q13 vol14/12
  title questions all flip to miss in RU while EN holds). Consistency 0.55
  confirms the variants diverge across languages instead of converging.
- Ceiling is question-type, not chain: title-match (q07, q11, q13, q15) hits
  on all chains; abstract nouns (q01 ambition, q05 happiness, q16 meaning of
  life) miss on all chains. Retrieval quality is dominated by bank phrasing vs
  chunk vocabulary, not by chain cleverness.

## When complexity paid

- Rerank: yes. +8pp overall, ~zero latency cost (cross-encoder 12-pair CPU
  rescore disappears inside 1b generation time: 4.3s vs 4.2s), no new failure
  mode. Demo chain for Phase 6.
- Multi-query: no. Two generator calls per question (rewrite + answer), +60%
  latency, worse RU, worst consistency. The no-query-translation decision
  (0011) stands — EN→RU is 0.90–1.00 without it for every chain except
  multi-query, whose problem is drift, not language.
- Persona cost is confirmed orthogonal: identical hits to naive (same
  retriever) at 2× latency (8.7s — longer voice outputs), so persona is a
  style tax, not a retrieval choice.

## Eval-design lessons

- Work-level (not chunk-level) expected sources survived first contact:
  q19 (Levin/faith, expected vol9 Анна Каренина) hits via vol8 chunks on
  several chains — volume-strict scoring would have false-negatived a
  multi-volume work. Volume displayed, work matched. Correct call from 0011.
- Cross-encoder id fixed at build time:
  `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, CPU batch 32, no GPU, no
  latency problem. LLM-as-reranker rejection (0011 Alternatives) validated —
  a 1b judge would have cost a third generator call per query.
- Runner resilience paid off again: 0 timeouts this run (vs 6/60 in Phase 4),
  but the ERROR-cell path was exercised in smoke tests and stayed green.
- Refusal metric needs a stricter scorer: `is_refusal` (empty sources +
  marker) correctly scores p01 RU as FAIL — the chain answered about
  smartphones with a fabricated "[3]" citation. The 0.55 gate catches
  gibberish (Phase 4) but not fluent off-topic; the probe that matters most
  is the one that hallucinates politely. Recorded, not solved — same as
  Phase 4, now measured (3/6).

## What failed / needed fixing during build

- `tests/test_compare_report.py` pinned bank == 10; bank growth to 20 broke
  it. Fix: Phase 4 tests pin the frozen q01–q10 subset (reports are
  point-in-time artifacts, the bank is living).
- `MultiQueryChain.__init__` resolves the variant count to a local before
  building the default `rewrite_fn` lambda (avoids call-time dependence on
  attribute assignment order).
- Rerank/multi-query reuse the `naive` template voice deliberately (retrieval
  is the experiment); no new template files, `list_templates` unchanged.

## Open threads for Phase 6

- Demo on `rerank`; keep losers with numbers (0012: comparison is the teaching
  value).
- q02 phrasing pair ("говорит о смерти" hits, "описывает смерть" misses) is a
  ready-made chunking/embedding case study for the lessons note.
- Refusal gate beyond scores (e.g. probe-driven threshold, self-check) is
  explicitly future work, not a Phase 5 gap to chase now.
