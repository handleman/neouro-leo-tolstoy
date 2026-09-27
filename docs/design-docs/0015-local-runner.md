# 0015: Local runner — one-command setup and chat for fresh clones

- Status: Draft
- Date: 2026-09-27
- Author: software-architect skill

## Context

A developer who just cloned the repo faces a multi-runtime obstacle course
before talking to Tolstoy: Python venv + `pip install -e ".[dev]"` + `.env`
copy + Ollama model pull + `npm install` in `web/` + manifest/clean/index
builds (gated on the gitignored 22-EPUB corpus in `data/raw/`) + a
background API process + the Node chat REPL. The Phase 6 README quickstart
documents every step, but documentation is not automation: order matters,
the corpus gate fails late today (at index time, not at setup time), and the
API's background lifecycle is left to the user. Goal: `make chat`-level
simplicity with no new dependencies and no behavior changes to existing
commands. Constraints: macOS/Linux contributors, Python 3.11+, Node 18+,
Ollama running locally, corpus placed manually (never committed, never
downloaded — see `data-sources.md`).

## Decision / Proposal

A root **`Makefile` is the single local runner** (no root `package.json`,
no shell-script bundle, no new tooling). Bare `make` prints `help`.
Contract — targets, owners, and chaining (recipes wrap the exact README
commands, unchanged):

- `make setup` — Python side: create `.venv` if missing, bootstrap pip via
  `ensurepip` when the venv has none (e.g. uv-managed trees), `pip install
  -e ".[dev]"`, copy `.env.example` → `.env` if missing (never overwrite),
  satisfy `ollama pull llama3.2:1b`, `npm install` in `web/`. Idempotent:
  safe to re-run; reports what it skipped and why.
- `make check-corpus` — fail-fast gate: asserts `data/raw/` holds the 22
  EPUB volumes. Every downstream target that needs text depends on it, so a
  corpus-less clone fails in seconds with the `data-sources.md` pointer —
  not 10 minutes into an index build.
- `make index` — depends on `check-corpus`: manifest build → clean `--all`
  → index `build --all` (the 26,188-chunk `.chroma/` store). Skips rebuild
  when `.chroma/` is already populated unless `make reindex` is asked
  (safe: upserts are idempotent on `chunk_id`, so rebuilds never duplicate).
- `make chat` — depends on `index`: starts the API (`uvicorn
  tolstoy.api.app:app` on :8000, background, no PID file — a shell `trap` on
  EXIT/INT/TERM owns the lifecycle, API log at `/tmp/tolstoy-api.log`), waits
  for `/health` OK, then runs the Node REPL (`--lang ru --chain rerank`, the
  Phase 5 winner) in the foreground. On REPL exit the API is stopped, so no
  orphaned uvicorn survives a closed laptop lid. `CHAT_LANG=` /
  `CHAT_CHAIN=` overrides select language and chain (deliberately *not*
  `LANG=`/`CHAIN=` — `LANG` is set by the shell locale).
- `make eval`, `make test` — thin wrappers over `python -m tolstoy.evaluate`
  and `pytest` + `ruff check` + `npm run typecheck`, for the gates in 0011
  and 0012.
- `make help` (default) — one-line description per target.

Ownership stays where it is: Python owns brain commands, Node owns the REPL,
Make owns ordering and lifecycle only. The `.env` keys in `config.py` /
`.env.example` remain the single settings source; the Makefile reads no
settings, it only passes `CHAT_LANG`/`CHAT_CHAIN` through to existing CLI
flags. README quickstart is rewritten to call the Makefile targets (the manual
commands stay documented as the fallback/under-the-hood reference).

## Alternatives

- **Root `package.json` scripts (`npm run setup/chat`)** — rejected:
  Node-centric entry for a Python-majority repo; venv activation and
  background-process lifecycle are awkward in npm scripts; splits the source
  of truth across two package managers. `web/package.json` keeps Node-only
  tasks (`chat`, `typecheck`).
- **Plain shell scripts (`setup.sh`, `chat.sh`)** — rejected: zero
  discoverability (no `help` equivalent), dependency ordering reimplemented
  by hand in each script, lifecycle handling duplicated. Closest runner-up;
  acceptable only if Make proves unavailable on a contributor machine.
- **Python-based runner (invoke / typer CLI, `pip install` plugin)** —
  rejected: adds a dev dependency to solve a problem `make` solves with
  zero installs; heavier than the task (this is a self-education repo, and
  the runner must be readable in one sitting).
- **Docker Compose one-liner** — rejected: contradicts local-first v1
  (Ollama + Chroma already run natively per 0006/0014); containerizing the
  demo adds image maintenance without removing any real step.

## Consequences

- Fresh-clone path becomes: prerequisites → `make setup` → place corpus →
  `make chat`. First-run failures collapse to one case (missing corpus) with
  one message.
- Easier: onboarding, demo repeatability, gate running (`make test/eval`).
  Harder: none structurally — recipes are thin; every wrapped command keeps
  working standalone.
- Follow-ups: README rewrite to Makefile-first; the corpus itself stays
  manual (out of scope — licensing/distribution question, not a runner
  question).

## Open questions

1. Windows support — out of scope (contributors on macOS/Linux); if needed,
  revisit the shell-script fallback, not WSL instructions.
2. ~~API PID-file location and stale-PID recovery~~ — resolved at build time:
  no PID file; shell `trap` owns the API process, log at `/tmp/tolstoy-api.log`.
3. ~~`--fresh` reindex flag vs separate target~~ — resolved: explicit
  `make reindex` (safe via idempotent upserts).
