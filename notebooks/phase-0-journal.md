# Phase 0 journal — dev environment

Date: 2026-09-20. Plan: `docs/design-docs/0006-phase-0-dev-environment.md`.

## Tool versions

- Python 3.14.7 (stack requires 3.11+ — OK). Package manager: `uv` 0.12.17
  (installed via astral installer mid-phase; initial `pip` venv discarded and
  recreated with `uv venv` + `uv pip install -e ".[dev]"` — identical 105
  packages, gate re-verified green). `pyproject.toml` is manager-agnostic.
- Node v24.20.0 (stack requires 20+ — OK), npm workspace `web/`, `tsx` + `typescript` strict.
- Ollama client 0.34.2, server started via `ollama serve` (was not running at entry, as assumed).
- Installed: fastapi, uvicorn, chromadb, sentence-transformers 6.1.0 (torch 2.14, cp314 wheels exist — Python 3.14 works), ebooklib, httpx, pydantic, pytest 9.1.1, ruff.

## Winning models

- Chat default: `llama3.2:1b` (stays in `.env.example`). RU smoke test answered in Russian and on-topic, but with a mid-word English slip ("happiness") and hallucinated book titles — expected for 1B with no context. Verdict: PASS with caveats; RAG must do the grounding in Phase 3. Revisit if voice is unusable there (`qwen2.5:1.5b` remains the fallback candidate; host also has `qwen3.5:9b` for later experiments, out of v1 scope).
- Embedding model: `paraphrase-multilingual-MiniLM-L12-v2` confirmed. Smoke: RU + EN sentences → 384-dim non-empty vectors, cosine(RU, EN) = 0.9109 — strong cross-lingual signal for the Phase 2 EN→RU baseline.

## What worked

- Editable install, `/health` skeleton contract live (`{"status":"ok","mode":"skeleton","collection":"tolstoy-ru"}`), pytest (5 passed) + ruff + `tsc --noEmit` all green, Node stub prints API URL and exits.

## What failed / needed fixing

- `tsc` stub failed first: `process` needs `@types/node` — added as devDependency (plan said "tsx + readline + fetch" stack; types package is implied tooling, no ADR needed).
- `ruff format` wanted `config.py` reflowed — applied, gate green after.
- pytest shows two upstream deprecation warnings (fastapi/httpx testclient, anyio portal alias) — harmless, no action.
- `ollama pull` output is extremely chatty (progress spam); journal notes it, no action.
