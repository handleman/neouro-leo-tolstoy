# Phase 3 journal — naive chat, first chain

Date: 2026-09-24. Plan: `docs/design-docs/0009-phase-3-naive-chat.md`.

## Result

`POST /chat` + `npm run chat` live against 26,188 chunks; RU + EN sessions
with RU citations; all error paths demonstrated; `pytest` 52 passed, `ruff`
clean, Node `typecheck` clean. Transcripts:
`evals/reports/phase-3-transcripts.md`.

## What worked

- Exact build order from 0009 held: Ollama client → chain → API → CLI.
  No interface rework needed; `CHAIN_REGISTRY = {"naive": ...}` is ready for
  Phase 4 entries.
- New config keys (convention: every tunable in `config.py` +
  `.env.example` + `KNOWN_ENV_KEYS`): `TOLSTOY_GENERATOR_TIMEOUT=60`,
  `TOLSTOY_CHAT_CONTEXT_CHARS=6000` (top_k=4 × 900-char chunks ≈ 3600 max,
  so 6000 never truncates in v1 — budget logic tested with a 50-char budget
  in `test_chains.py` instead).
- EN→RU recall holds through the chat path: RU «Что Толстой говорит о
  смерти?» and EN «What does Tolstoy say about death?» cite the same 4 RU
  chunks; «What is death?» retrieves the «О жизни» treatise (0.65–0.71),
  the most on-topic grounding so far.
- `GeneratorUnavailable` → 503 verified live (dead-port Ollama URL) and in
  unit tests; empty retrieval refuses with no citations and never calls the
  generator.

## What failed / needed fixing

- **CLI EOF stack trace (found via piped stdin):** `rl.question` in a loop
  threw `ERR_USE_AFTER_CLOSE` on EOF. Rewrote the loop as `for await...of`
  over the readline interface. Second instance of the same race: an explicit
  `rl.prompt()` after a *fast* (422) answer fired after stream close.
  Fix: `inputClosed` flag guards `prompt()`; the iterator ends the loop on
  its own. Also removed a wrong `if (inputClosed) break` after `ask` — it
  dropped queued piped lines (fast error answers returned before queued
  input was consumed). Verified 3/3 clean exits.
- **Prompt-formatting nit:** `ruff format` reflowed the `build_prompt`
  ternary; run `ruff format` before finishing, not just `ruff check`.

## Prompt-stuffing observations (0009 Q1 first evidence)

- 6000-char budget is generous for top_k=4; stuffing order = retrieval order
  with `[n] том|work|chapter` headers (~40 chars overhead per chunk).
- llama3.2:1b RU answers are short paraphrases of the chunks (usable);
  EN answers are longer and mix translation with verbatim chunk echo —
  acceptable for v1, but the echo habit is why Phase 5 needs a faithfulness
  lens, not just hit-rate.
- Grounding failures (both logged in transcripts): (1) Natasha Rostova's
  fictional farewell recast as a "letter to Natacha de Rothschild";
  (2) mid-answer English word ("Especially") leaking into a RU answer.
  Both argue for the Phase 4 `cite-or-refuse` chain.

## Open for Phase 4

- `naive` gives the baseline prompt + registry; Phase 4 adds variants only.
- Refusal wording finalized here (`Не нашёл ответа...` /
  `I found nothing...`), reused by `cite-or-refuse`.
- 0009 Q2 (return RU original alongside EN) stays default-no in v1.
