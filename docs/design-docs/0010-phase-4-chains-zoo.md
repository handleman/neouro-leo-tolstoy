# 0010: Phase 4 — chains zoo + persona (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 3 exit (working `naive` chain, `/chat`, Node CLI). Goal: two more chains (`persona`, `cite-or-refuse`) built as config + prompt variants — not rewrites — and compared side by side on a fixed bilingual question set. Interfaces frozen: `ask(question, lang)`, `CHAIN_REGISTRY`, `/chat { question, lang, chain }`.

## Decision / Proposal

Build in this exact order.

### Step 1 — Prompt registry `tolstoy/chains/prompts/`

- Extract Phase 3's inline prompt builder into a shared helper (system + context + question assembly, truncation budget unchanged).
- Add versioned templates per chain per language: `naive.ru`, `naive.en`, `persona.ru`, `persona.en`, `cite-or-refuse.ru`, `cite-or-refuse.en` (plain-text template files, committed — prompts are versioned artifacts, diffable in review).
- `persona` templates: Tolstoy voice instructions (moral inquiry, peasant wisdom, long reflective sentences, concrete country images) added to the base instruction; retrieval identical to `naive`.
- `cite-or-refuse` templates: must-cite instruction plus refusal strings when retrieved scores fall below `TOLSTOY_SCORE_THRESHOLD` ("not in my works" in RU/EN).

### Step 2 — Chain modules + registry

- `tolstoy/chains/persona.py`: same retriever as `naive`, persona templates.
- `tolstoy/chains/cite_or_refuse.py`: same retriever, score-threshold gate (below threshold → refusal answer with empty `sources[]`, no generator call wasted on fabrication), cite-or-refuse templates.
- Registry becomes `{ naive, persona, cite-or-refuse }`; `/chat` `chain` param validates against it (unknown → 422, unchanged behavior).

### Step 3 — Question bank seed `evals/question_bank.json`

- 10 questions, each `{ id, ru, en, expected_work, notes }` (expected source = volume/work in the Russian corpus; roadmap seed bank is the starting content).
- Committed; grows to ~20 with expected chunk-level sources in Phase 5.

### Step 4 — Comparison runner (CLI `python -m tolstoy.compare`)

- Runs every chain × every question × both languages against `/chat` (or in-process), writes `evals/reports/phase-4-comparison.md`: per-question answers side by side with sources, plus author notes on style vs faithfulness and EN translation fidelity vs RU sources.
- Deterministic order; report committed.

### Tests (new/extend)

- `test_chains.py` (extend) — registry contains exactly the three chains; `persona` uses persona templates (RU+EN); `cite-or-refuse` refuses below threshold (answer matches refusal string, `sources == []`, generator not called) and answers above it.
- Prompt rendering test — every template renders for both langs with sample context (no missing placeholders).
- Comparison report exists and covers 3 chains × 10 questions × 2 langs (structural check, not quality judgment).

### Exit checklist

1. `/chat?chain=persona|cite-or-refuse` works in RU + EN via CLI.
2. `evals/reports/phase-4-comparison.md` committed: same 10 bilingual questions on 3 chains + style-vs-faithfulness notes.
3. Refusal behavior demonstrated (low-score query → clean refusal in both langs).
4. `pytest` + `ruff` green; `notebooks/phase-4-journal.md` written (system-prompt effects, temperature notes, refusal tuning).

## Alternatives

- **Fine-tune for voice instead of persona prompts** — out of scope (stack-decision): prompting gets ~80% of style for study purposes; fine-tuning waits until RAG + prompting plateau.
- **Per-chain retriever tuning now** — rejected: Phase 4 isolates prompt/style effects with retrieval held constant; retrieval variants are Phase 5.
- **LLM-as-judge scoring** — deferred to Phase 5 eval design; Phase 4 comparison is human-read notes.

## Consequences

- New chains are now provably cheap (registry + templates); the pattern scales to Phase 5.
- Threshold semantics from `cite-or-refuse` feed Phase 5 metrics (refusal precision).
- Question bank becomes the eval seed — quality of `expected_work` labels matters downstream.

## Open questions

1. Refusal threshold value — tuned here from live queries, recorded in config + journal.
2. Temperature per chain (persona wants more voice, cite-or-refuse wants less)? Default single value; per-chain override only with evidence.
3. Do comparison reports also store raw JSON? Default markdown only in v1.
