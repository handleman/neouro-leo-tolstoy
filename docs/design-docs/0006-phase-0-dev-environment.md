# 0006: Phase 0 — dev environment (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry assumptions: no code, empty `notebooks/`, host has Python 3.14, Node 24, Ollama client 0.34.2 installed but no running server. Stack requires Python 3.11+, Node 20+, Ollama, Chroma, one multilingual embedder, pytest + ruff, `pyproject.toml`, `.venv/`, `.chroma/`, `web/` workspace, `.env.example`. Phase 0 must end with a skeleton repo where `GET /health` passes and both models are proven downloadable — everything Phase 1+ builds on.

## Decision / Proposal

Build in this exact order; each step is verifiable before moving on.

### Step 1 — Python project skeleton (owner: Python)

1. Create `pyproject.toml`: project metadata, dependencies (`fastapi`, `uvicorn`, `chromadb`, `sentence-transformers`, `ebooklib`, `httpx`, `pydantic`), dev extras (`pytest`, `httpx` test client, `ruff`), pytest + ruff config sections.
2. Create virtualenv at `.venv/` (gitignored) and install the project editable with dev extras.
3. Create package skeleton: `tolstoy/__init__.py`, `tolstoy/config.py` (all settings from env with defaults per 0005 convention 1), `tolstoy/api/app.py` with `GET /health` only.
4. Phase 0 `/health` response contract: fields `status` (`"ok"`), `mode` (`"skeleton"` — replaced by store info in Phase 2), `collection` (configured name, uncreated). No Chroma/Ollama contact yet.

### Step 2 — Node workspace skeleton (owner: Node)

1. Create `web/package.json` (workspace package `tolstoy-chat`, scripts `chat`, `typecheck`), `web/tsconfig.json` (strict), `web/src/chat.ts` as a stub that prints the API base URL from env and exits (real REPL lands in Phase 3).
2. Verify `tsx` runs the stub and `typecheck` passes.

### Step 3 — Config surface (owner: Python, consumed by Node)

Create `.env.example` with every tunable and its default: API port and base URL, Chroma dir, collection name (`tolstoy-ru`), embedding model id, Ollama URL + model id, chat temperature, top-k, chunk size/overlap, refusal threshold. `tolstoy/config.py` is the single reader; Node reads only API URL + lang defaults from env.

### Step 4 — Model smoke tests (owner: Python)

1. Start Ollama server; pull the default chat model (`llama3.2:1b`); run a short Russian prompt smoke test (reads RU fluently, answers coherently). If it fails, pull candidate `qwen2.5:1.5b` and record the winner as the default in `.env.example`.
2. Download the default multilingual embedding model and embed one Russian + one English sentence; assert vectors are non-empty and same-dimension (cross-lingual baseline sanity for 0008).
3. Record both winning model ids in `.env.example` and in `notebooks/phase-0-journal.md`.

### Step 5 — Hygiene gate (owner: both)

`ruff check`, `ruff format --check` (or equivalent), `pytest` (skeleton tests, see below), `GET /health` returns the skeleton contract. Add/extend `.gitignore` entries: `.venv/`, `.chroma/`, `data/raw/`, `data/clean/`, `web/node_modules/`, `.env` (example stays committed).

### Tests (new files in `tests/`)

- `test_config.py` — defaults load with no env; overrides respected; all `.env.example` keys known.
- `test_api.py` (skeleton) — `GET /health` returns `status ok`, `mode skeleton` via FastAPI test client (no server needed).

### Exit checklist (all must pass)

1. Fresh clone → env setup → `GET /health` returns the skeleton contract.
2. `pytest`, `ruff`, Node `typecheck` all green.
3. Ollama serves the chosen RU-capable model; embedding model cached with RU/EN smoke vectors verified.
4. `notebooks/phase-0-journal.md` written (tool versions, winning models, what failed).

## Alternatives

- **Docker-compose for Ollama/Chroma** — rejected: Chroma is file-backed, Ollama already native; containers add ops with no learning value in v1.
- **Full `/search` + `/chat` skeleton now** — rejected: endpoints without store/generator invite fake-green tests; Phase 0 proves environment only.
- **Poetry instead of pip/uv + pyproject** — rejected: stack allows pip or uv; either satisfies `pyproject.toml`, no lock-tool war in Phase 0.

## Consequences

- Phase 1 gets an installable package, a config module, and proven model ids — no "works on my machine" ingest.
- `/health` contract will evolve (Phase 2 adds store info, Phase 3 adds Ollama reachability); the skeleton `mode` field makes that evolution explicit.
- Node has a compiling stub workspace ready for the Phase 3 REPL.

## Open questions

1. Winning Ollama default (`llama3.2:1b` vs `qwen2.5:1.5b`) — decided by the Step 4 smoke test at build time.
2. Confirm final multilingual embedding model id in Step 4 — default `paraphrase-multilingual-MiniLM-L12-v2` unless the smoke test disqualifies it.
3. `uv` vs `pip` for the venv — either; record the choice in the journal.
