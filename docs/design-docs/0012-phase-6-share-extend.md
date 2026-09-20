# 0012: Phase 6 — share & extend (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 5 exit (measured winner, eval reports, 5 chains). This phase writes no RAG logic (except the optional EN experiment). Goal: make the project demonstrable to a stranger and decide its future (web UI vs framework migration, EN corpus or RU-only forever). All artifacts are docs + transcripts + a README demo.

## Decision / Proposal

Execute in this exact order.

### Step 1 — Demo transcripts

- Capture two CLI sessions with the winning chain and commit as `evals/reports/demo-transcript-ru.md` and `demo-transcript-en.md`: same questions in both languages, answers with numbered RU sources, translation markers visible in the EN session, plus one refusal demonstration.
- Transcripts are curated (best representative session), not cherry-picked per answer — note the date, model id, and chain in each file header.

### Step 2 — README demo section

- Extend `README.md`: what it is, 5-minute quickstart (env setup → index → chat), one RU + one EN example exchange with sources, link to design docs and eval reports. No new claims beyond measured Phase 5 results.

### Step 3 — Lessons-learned note

- Write `docs/design-docs/0013-lessons-learned.md` (ADR-style: what we tried per phase, what worked/failed and why, builder's judgment): hand-rolled vs framework verdict, chunking/embedding takeaways, tiny-model limits, bilingual-chat findings, what to do differently.
- This is the project's real output (vision: "the learning artifact"); each phase journal feeds it.

### Step 4 — Future decisions (documented, not built)

- Web UI vs LangChain migration: decision inputs (what hurts now, what a framework would/wouldn't fix), recorded in the lessons note as a proposal — no code.
- Service deployment: build-or-defer call on the future online service (hosting, edge auth, packaging) — v1 was kept compatible per 0014, so this decides timing, not redesign. Recorded in the lessons note — no code.
- Optional English corpus (`tolstoy-en`, decision 0004): build-or-close call. If build: Gutenberg download script, MiniLM model, `tolstoy-en` collection, manifest EN fields, comparison report vs generator translation. If close: record RU-only-forever with rationale. Either way the decision is written down.

### Tests / gates

- No new code tests. Gates: transcripts render correctly from committed sessions; README quickstart verified on a fresh clone; all phase journals + reports present and linked.

### Exit checklist

1. README demo section merged; quickstart verified from scratch.
2. RU + EN demo transcripts committed with model/chain/date headers.
3. `0013-lessons-learned.md` written; web-UI/framework and EN-corpus decisions recorded.
4. Repo state tagged as v1 (maintainer's call) — roadmap complete.

## Alternatives

- **Building the web UI in this phase** — rejected: the decision is the deliverable; building it starts a new project, not ends this one.
- **Skipping transcripts (README examples hand-written)** — rejected: transcripts must be real CLI output or they prove nothing; curation is allowed, fabrication is not.
- **Deleting losing chains** — rejected: losers stay with their eval numbers; the comparison is the teaching value.

## Consequences

- Strangers can run the demo and read the full story (design docs → evals → lessons).
- Future work (web UI, frameworks, EN corpus) starts from written decisions, not vague intent.
- The repo becomes a portfolio piece: local-first RAG, measured, bilingual, cited.

## Open questions

1. v1 tag name/timing — maintainer's call at build time.
2. EN corpus build-or-close — decided here with the evidence from Phases 2–5.
3. Web UI stack (if approved later) — out of scope; a new design doc starts it.
