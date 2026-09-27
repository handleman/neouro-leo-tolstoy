# 0013: Lessons learned — local-first RAG on Tolstoy (v1 retrospective)

- Status: Draft
- Date: 2026-09-26
- Author: builder (feeds: `notebooks/phase-0` through `phase-5` journals)

## Context

v1 is done: 6 phases, 22 Russian EPUB volumes → 26,188 chunks in `tolstoy-ru`
→ 5 hand-rolled chains → measured on a 20-question bilingual bank
(`evals/reports/phase-5-eval.md`: rerank 0.55, naive/persona/cite-or-refuse
0.47, multi-query 0.38; EN→RU consistency 0.90–1.00 except multi-query 0.55).
Vision called this repo "the learning artifact" — this note is that
artifact: what we tried per phase, what worked/failed and why, and the
builder's judgment on what to do differently. Source of every claim is the
phase journal or the eval report it cites; no new claims are made here.

## Decision / Proposal

### Per phase: tried → worked / failed

- **Phase 0 (env):** Python-brain + Node-mouth split, env-driven config,
  Ollama + embed smoke test. Worked: the split never caused a single
  cross-boundary bug in 6 phases; `GET /health` caught every bad state first.
- **Phase 1 (ingest):** OPF spine order, `kind: work` vs `editorial`,
  manifest with SHA + work lists. Worked: provenance questions never arose
  again; `data/clean/` rebuilds deterministically. Lesson: manifest-first
  pays off the moment the bank needs grounding (Phase 5 q11–q20 came straight
  from `work_list`).
- **Phase 2 (baseline retrieval):** chunk 900/150, one multilingual embedder,
  `POST /search` + REPL before any LLM existed. Worked: the REPL built the
  cosine intuition that later explained every miss (q02 pronoun phrasing
  misses Ivan Ilyich while "Что Толстой говорит о смерти?" hits — wording
  sensitivity, not model failure). Failed: assumed top-4 cosine is "good
  enough" — Phase 5 measured it at 0.47.
- **Phase 3 (naive chat):** stuff-everything → 1b generator, `{question,
  lang}`, RU citations under EN answers. Worked: end-to-end grounding is real
  (demo transcripts cite vol/chunk/scores). Failed first: unbounded
  generation loops on the 1b model — fixed same-day via `NUM_PREDICT` /
  `REPEAT_PENALTY` caps (phase-4b re-run: timeouts 6→0).
- **Phase 4 (chains zoo):** persona + cite-or-refuse via template key +
  threshold only, shared `StuffChain`. Worked: "config + prompt variants, not
  rewrites" held literally — 3 chains, zero retriever changes. Found: the
  0.55 score gate catches gibberish (RU 0.49 / EN 0.38) but not fluent
  off-topic ("квантовая механика" scores 0.60, inside the on-topic band).
- **Phase 5 (quality + eval):** harness first, then rerank + multi-query.
  Worked: work-level (not chunk-level) expected sources — q19 (Levin/faith,
  expected vol9) hits via vol8 chunks, which volume-strict scoring would have
  false-negatived. Rerank pays (+8pp at ~zero latency cost). Failed:
  multi-query (RU 0.30, consistency 0.55) — RRF over generator rewrites
  drifts off title-match anchors. Refusal measured honestly: 3/6 probes, with
  the worst cell (p01 RU smartphones) hallucinating *with a fake citation*.

### Hand-rolled vs framework verdict

Stay hand-rolled for v1 and until a second consumer forces the question. The
evidence: 5 chains in ~6 small files with full score-order visibility (the
q01 rerank observation — CE order ≠ cosine order — is debuggable *because*
both scores are on the table); 71 tests, all stubbed, running in ~1s with no
model downloads; zero dependency churn across 6 phases. A framework would
have standardized the retrievers but hidden exactly the layer this project
exists to teach, and it would not fix the actual weakest link (the refusal
gate is a scoring problem, not a plumbing problem). If a web UI is ever
approved, revisit — a second consumer with streaming/auth/pagination needs is
the honest trigger, not chain count.

### Chunking / embedding takeaways

- 900/150 was never re-tuned and never needed to be: retrieval quality is
  dominated by query phrasing vs chunk vocabulary, not by ±200 chars of
  window. The q02 phrasing pair is the case study to keep.
- One multilingual embedder for RU chunks + EN queries was sufficient
  (EN→RU 0.90–1.00 without any query translation). Separate EN/RU vector
  spaces would have added ops for no measured gain.
- Work-level eval granularity is the durable choice under re-chunking; chunk
  ids churn, work names don't (except multi-volume works, which is why the
  scorer matches on work and displays volume).

### Tiny-model (1b) limits

- The generator is a translator/summarizer, not a reasoner: grounded answers
  with real citations when retrieval hits; code-switching (`Xadhi-Murat`,
  `Sergius`, `Cold`), loop attractors, and false memories ("my wife Levna")
  when it strains. Caps (`NUM_PREDICT`, `REPEAT_PENALTY`) bound the damage;
  temperature 0.3 single-value for all chains was enough.
- Generation dominates latency (~1–16s variance); retrieval and even
  cross-encoder rescoring disappear inside it. Optimize the generator call or
  nothing.
- Persona is a 2× latency style tax (8.7s vs 4.2s) with identical hits — a
  product decision, never a retrieval decision.

### Bilingual-chat findings

- RU-primary with on-demand EN translation (0003) validated end to end:
  same RU chunks cited under both languages, translation markers visible,
  consistency 0.90–1.00 for 4/5 chains.
- The EN weak link is generation fidelity, not retrieval: Q3 EN (Sergius)
  retrieves 3/4 Отец Сергий yet talks about Nikodim and Anna Karenina. Fix
  direction is prompt-side (tighter translation instruction), not
  corpus-side — which is one reason the EN corpus closes below.

### What to do differently

1. Build the eval harness in Phase 2, not Phase 5 — four phases ran on vibes
  that 0.47 would have corrected on day one.
2. Freeze report-coupled tests to question-id subsets from the start (learned
  the hard way when the bank grew 10→20 and broke Phase 4 tests).
3. Probe refusal with *fluent* off-topic from the beginning; gibberish probes
  flatter the gate.

### Future decisions (0012 step 4 — documented, not built)

- **Web UI vs LangChain migration: DEFER both.** Inputs: nothing structural
  hurts (CLI + API cover the demo; registry carries new chains without API
  changes); a framework fixes plumbing, while the open problems are scoring
  (refusal gate) and prompts (EN fidelity) — out of framework scope. Revisit
  trigger: approval of a web UI, which starts a new design doc (stack
  undecided here).
- **Service deployment: DEFER.** v1 was kept compatible per 0014
  (env-driven config, CORS allowlist, typed 422/404/503) so timing — not
  redesign — is the only future call. No hosting, edge-auth, or packaging
  work in v1.
- **English `tolstoy-en` corpus: CLOSE (RU-only-forever for v1).**
  Rationale from Phases 2–5 evidence: EN→RU recall is 0.90–1.00 with no EN
  corpus and no query translation; generator-side translation of RU-grounded
  answers works (fidelity caveats are prompt-side); a Gutenberg collection
  would double index ops, need its own embedder (0003: never mix EN/RU
  vectors), and buy a comparison experiment nobody needs once the winner is
  measured. Reopen only if EN→RU recall ever regresses below ~0.8 on a
  future bank.

## Alternatives

- **Migrating to LangChain now** — rejected: standardizes retrievers, hides
  the teaching layer, fixes none of the open problems (refusal scoring, EN
  fidelity, 1b limits).
- **Building the EN corpus "for completeness"** — rejected: cost without a
  measured gap; the bilingual contract (0003) is already satisfied by
  cross-lingual retrieval + generator translation.
- **Deleting losing chains (multi-query)** — rejected per 0012: losers stay
  with their numbers; the comparison is the teaching value.

## Consequences

- Repo is a portfolio piece as-is: local-first, measured, bilingual, cited;
  README demo + transcripts let a stranger run it.
- Any future work (web UI, frameworks, EN corpus) starts from written
  decisions with triggers, not vague intent.
- The eval bank + harness is the regression suite for future tuning.

## Open questions

1. v1 tag name/timing — maintainer's call (all technical gates are met).
2. Refusal beyond score gates (probe-driven threshold, generator
  self-check) — future work item, needs its own design doc, not a v1 gap.
3. Chunk-size retuning — never needed; the harness exists if anyone wants
  to try.
