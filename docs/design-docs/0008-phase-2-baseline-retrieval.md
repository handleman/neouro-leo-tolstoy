# 0008: Phase 2 — baseline retrieval, Russian-only (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 1 exit (`data/clean/vol*.json` + committed manifest, 22 vols). No LLM in this phase. Goal: chunk → embed → Chroma (`tolstoy-ru` only) plus a working `/search` endpoint and a REPL that proves RU and EN queries both retrieve RU chunks (cross-lingual baseline for 0003). Single multilingual embedding model (id fixed in Phase 0).

## Decision / Proposal

Build in this exact order.

### Step 1 — Chunker `tolstoy/ingest/chunk.py`

- Input: `data/clean/vol{NN}.json` sections with `kind == work` only (`editorial` never chunked in v1).
- Rule: ~900 chars with ~150 overlap (config `TOLSTOY_CHUNK_SIZE`, `TOLSTOY_CHUNK_OVERLAP`); split on paragraph boundaries where possible so Tolstoy's long paragraphs stay intact; never merge across a `work`/`chapter` boundary or across volumes.
- Output record: `{ chunk_id, text, volume, work, chapter, spine_index, kind: "work" }`; `chunk_id = ru-vol{NN}-{work-slug}-{spine_index}-{ordinal}` (deterministic; same text → same ID across runs).

### Step 2 — Embedder `tolstoy/store/embed.py`

- Lazy singleton loader for the configured multilingual model; batch-encode API `embed(texts[]) → vectors[]`; query API `embed_query(text) → vector` (same model — corpus and queries share it).
- No English model, no second path in v1.

### Step 3 — Store wrapper `tolstoy/store/chroma.py`

- Persistent Chroma client at `TOLSTOY_CHROMA_DIR` (`.chroma/`, gitignored); single collection `tolstoy-ru` (from `TOLSTOY_COLLECTION`).
- `upsert(chunks[], vectors[])` idempotent on `chunk_id`; `query(vector, top_k, filter?)` with cosine similarity, optional metadata filter `{ volume, work }` (chapter optional).
- Unknown-collection requests are rejected with "not built yet" (contract for the deferred `tolstoy-en`).

### Step 4 — Index CLI `python -m tolstoy.index`

- Commands: `build [--volume NN | --all]` (clean → chunk → embed → upsert, logs counts per volume), `stats` (collection count, per-volume breakdown), `reset --yes` (drop + rebuild, danger-guarded).
- Full 22-vol build is the phase's heavy step; per-volume mode enables fast iteration.

### Step 5 — API: `/health` upgrade + `POST /search`

- `/health` response now: `status`, `mode: "retrieval"`, `collection`, `chunk_count`, `embed_model` (no Ollama fields until Phase 3).
- `POST /search` request: `query` (required, non-empty), `collection` (default `tolstoy-ru`; anything else → 404 "not built yet"), `top_k` (default 4, clamped 1–20), `filter` (optional `{ volume, work }`).
- `POST /search` response: `collection` + `results[]`, each `{ chunk_id, text, score, volume, work, chapter }` ordered by score desc. Validation failures → 422.

### Step 6 — Search REPL `python -m tolstoy.search`

- Loop: prompt → embed → query → print top-k with scores + `volume/work/chapter/chunk_id`. Flags `--top-k`, `--filter work=...`. This is the learning surface for chunk/overlap/cosine intuition (run before any LLM exists).

### Tests (new files)

- `test_chunk.py` — determinism (same input → same IDs/texts); overlap honored; no chunk crosses work/chapter/volume boundaries; editorial sections excluded.
- `test_store.py` — upsert twice → no duplicates; filtered query respects `volume/work`; unknown collection → "not built yet"; score ordering desc.
- `test_api.py` (extend) — `/health` retrieval contract; `/search` happy path, 422 on empty query, 404 on `tolstoy-en`, filter honored (via test client with a tiny fixture collection).

### Exit checklist

1. `python -m tolstoy.index build --all` completes; `stats` shows all 22 volumes with sane per-volume counts.
2. Seed question RU («Что Толстой говорит о смерти?») returns Ivan Ilyich / War and Peace chunks; same question in EN retrieves the same RU chunks (cross-lingual baseline proven, logged in journal).
3. `POST /search` exercises (happy path, filter, 404, 422) all behave per contract.
4. `pytest` + `ruff` green; `notebooks/phase-2-journal.md` written (chunk-size observations, cosine-score reading, EN→RU recall notes).

## Alternatives

- **Sentence-level chunking** — rejected for v1: char-window with paragraph awareness preserves Tolstoy's long-sentence flow and is simpler to reason about; revisit if evals show boundary damage.
- **In-memory Chroma** — rejected: persistent `.chroma/` survives restarts and makes `stats`/`reset` meaningful; zero extra ops.
- **Separate query-translation step for EN queries** — rejected for v1 (0003): multilingual embeddings cover the baseline; translation pre-step is a Phase 5 multi-query candidate.

## Consequences

- Phase 3 gets a queryable store, a stable chunk-ID scheme for citations, and proven EN→RU recall.
- Chunk size/overlap stay tunable via config; any change requires re-index (`reset` + `build`) and is logged in the journal.
- `.chroma/` is local-only and gitignored; any machine reproduces it via `index build --all`.

## Open questions

1. Chunk-size tuning (900/150 default) — first evidence comes from the Step 6 REPL sessions in this phase.
2. `kind: editorial` opt-in search filter — expose or keep hidden? Default hidden in v1.
3. Query-time score threshold — not enforced in v1 retrieval; `cite-or-refuse` adds it in Phase 4.
