# Phase 2 journal — baseline retrieval, Russian-only

Date: 2026-09-23. Plan: `docs/design-docs/0008-phase-2-baseline-retrieval.md`.

## Result

`python -m tolstoy.index build --all` → 26,188 chunks, all 22 vols
(`stats` per-volume: vol01 1265 … vol21 159, vol22 415 — diary vols
legitimately thin). `POST /search` + `python -m tolstoy.search` live;
`pytest` 38 passed, `ruff` clean. Cross-lingual baseline proven: RU
«Что Толстой говорит о смерти?» and EN «What does Tolstoy say about
death?» retrieve the same 4 RU chunks (letters + «Божеское и
человеческое»); targeted «смерть Ивана Ильича» hits vol12 ch I/II/VI/VII
at 0.71–0.77.

## What worked

- Paragraph-aware packer (900/150 from config): every chunk ≤ 900 chars,
  deterministic IDs (`ru-vol{NN}-{slug}-{spine}-{ord}`), no chunk crosses
  a work/chapter/volume boundary (per-section chunking).
- Cosine-space Chroma (`tolstoy-ru`, `.chroma/` gitignored); upsert
  idempotent on `chunk_id`; `reset --yes` + `build --volume NN` made
  iteration cheap. Full build took minutes on CPU.
- API seams (`embed_query_text` / `run_search_query` module indirection)
  keep unit tests model-free; live TestClient run confirmed
  happy-path / 422 / 404 / filter against the real 26k store.

## What failed / needed fixing

- **Duplicate-emit bug (found via identical scores):** when carried
  overlap + new paragraph still exceeded 900 chars, the packer emitted
  the carry a second time → 2,773 duplicate texts (9% of the first
  30,904-chunk build), surfacing as 4 identical 0.7305 scores. Fix: drop
  the carry at that boundary (overlap is best-effort; bounded chunks
  matter for the 512-token embedder). Rebuilt from `reset`.
- **Signature noise:** 498 sub-100-char chunks, mostly letter closings
  («Л. Т.» 15x, «Лев Толстой.» 6x) — identical tiny vectors drowned
  top-k. Fix: `TOLSTOY_CHUNK_MIN_CHARS=50` (new key in
  `config.py` + `.env.example` + `KNOWN_ENV_KEYS`; config test still
  green). Deviation from 0008, logged here.
- Broad seed question surfaces letters over Ivan Ilyich — honest
  baseline behavior (query literally matches letter content + the
  «Толстой» signature term), not a bug; targeted queries rank correctly.

## Chunk/overlap observations (0008 Q1 first evidence)

- ~900 chars ≈ a few Tolstoy paragraphs; long single paragraphs
  hard-split cleanly (max len exactly 900 post-fix).
- Cosine scores: on-topic literary hits 0.65–0.77; EN→RU parity within
  ~0.04 of RU scores (multilingual MiniLM-L12 holds up).
- Score threshold deliberately unenforced (0008 Q3 stays open for the
  Phase 4 `cite-or-refuse` chain).

## Open for Phase 3

- `naive` chain gets: stable chunk IDs for citations, proven EN→RU
  recall, `/search` + REPL as debug surfaces.
- 0002 Q2 (footnote sidecar link schema) still open; sidecars carry
  spine_index + head only.
- `.chroma/` is local-only; any machine reproduces via `index build --all`.
