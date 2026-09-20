# 0009: Phase 3 — naive chat, first chain (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 2 exit (queryable `tolstoy-ru`, `/search` working, EN→RU recall proven). First LLM contact. Contracts from 0003: `ask(question, lang) → { answer, sources[], answer_lang }`, `lang` defaults `ru`, `lang=en` translates the RU-grounded answer with RU citations. Python owns chains + API; Node owns the CLI surface.

## Decision / Proposal

Build in this exact order.

### Step 1 — Ollama client `tolstoy/generate/ollama.py`

- Single `generate(system, user, options?) → text` call against `TOLSTOY_OLLAMA_URL` / `TOLSTOY_OLLAMA_MODEL`; temperature from config (default ~0.3); request timeout configured; Ollama-down maps to a typed `GeneratorUnavailable` error (API turns it into 503, never a fake answer).
- No retries with different models in v1; model swap is one env var.

### Step 2 — Chain interface `tolstoy/chains/base.py` + `naive.py`

- `Chain` interface: `name` + `ask(question, lang) → { answer, sources[], answer_lang }`; `CHAIN_REGISTRY = { "naive": NaiveChain }` (grows in Phases 4–5); unknown `chain` → 422.
- `NaiveChain.ask`: embed question (same multilingual model) → retrieve top-`k` (default 4, no filter, no threshold) → build prompt → generate → attach sources `{ chunk_id, volume, work, chapter, score }`.
- Prompt builder (in `naive.py` for v1; extracted to shared helper when Phase 4 adds variants): system instruction per `lang` (`ru`: answer in Russian as Tolstoy, cite volume/work/chapter; `en`: answer in English as a translation of the cited Russian passages, say so), then stuffed context chunks (ordered, truncated to a configured char budget so tiny-model context never overflows), then the question.

### Step 3 — API: `POST /chat`

- Request: `question` (required, non-empty), `lang` (`ru|en`, default `ru`), `chain` (default `naive`), `collection` (default `tolstoy-ru`; anything else → 404 "not built yet").
- Response: `answer`, `answer_lang`, `chain`, `sources[]` (`chunk_id, volume, work, chapter, score`).
- Errors: 422 validation / unknown chain / bad lang; 404 unknown collection; 503 generator unavailable. `/health` gains `ollama_model` + `ollama_reachable`.

### Step 4 — Node CLI `web/src/chat.ts`

- Package `tolstoy-chat`; `tsx`-run `chat` script; flags `--api`, `--lang ru|en` (default `ru`), `--chain`.
- REPL: readline loop, `/en` + `/ru` switch answer language, `/chain <name>` switch chain, `/quit` exit; renders answer, then numbered sources (`volume/work/chapter/chunk_id/score`); for `answer_lang == en` prints a "translated from RU sources" marker.
- Transport errors (422/404/503, connection refused) render as human-readable lines, never stack traces.

### Tests (new files; generator stubbed — no Ollama in tests)

- `test_chains.py` — `NaiveChain.ask` with stubbed retriever + stubbed generator: sources attached in order; `lang=en` system instruction requests translation; empty retrieval → answer says nothing found (no fake citations).
- `test_api.py` (extend) — `/chat` happy path (stubs), 422/404/503 mapping, `answer_lang` echo.
- CLI: manual session checklist (RU session + EN session, language switch, error display) saved as `evals/reports/phase-3-transcripts.md`.

### Exit checklist

1. End-to-end RU conversation with visible Russian sources via the Node CLI.
2. Same via `--lang en`: English answers citing the same RU chunks, marked as translated.
3. All error paths demonstrated (bad chain, unknown collection, Ollama stopped → clean 503 line).
4. `pytest` + `ruff` + Node `typecheck` green; `notebooks/phase-3-journal.md` written (prompt-stuffing observations, tiny-model context limits, grounding failures).

## Alternatives

- **Streaming responses (SSE)** — deferred: plain JSON keeps the v1 contract comparable across chains; streaming is a CLI enhancement for Phase 6.
- **LangChain LCEL for the chain** — rejected for v1 (stack-decision): the hand-rolled `ask()` is the learning object; registry pattern gives the same swappability.
- **Separate translator model for `lang=en`** — deferred to Phase 5+ (0003): generator translation suffices while answers are short and cited.

## Consequences

- v1 is shippable after this phase: chat with citations, bilingual, fully local.
- Phase 4 adds chains as registry entries + prompt variants only — no interface changes.
- Prompt-budget truncation behavior learned here bounds all later chains.

## Open questions

1. Context char budget for stuffing (model-context vs answer quality) — set from Step 2 experiments, recorded in journal.
2. Should `lang=en` also return the Russian original alongside? CLI UX call (0003 Q3) — default no in v1.
3. Refusal wording for empty retrieval ("not in my works" RU/EN) — finalized here, reused by `cite-or-refuse`.
