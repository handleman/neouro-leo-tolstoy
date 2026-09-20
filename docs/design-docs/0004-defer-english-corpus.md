# 0004: Defer English Gutenberg corpus (Phase 2 is Russian-only)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

After 0002 (EPUB ingest) and 0003 (Russian-primary bilingual chat), the maintainer decided Phase 2 must not build English texts: no Gutenberg downloads, no `tolstoy-en` collection, no English embedding model in Phases 1–2. The 22 Russian EPUB volumes in `data/raw/` are the sole corpus for v1. English stays only as generator-rendered translation (`lang=en` over Russian chunks, per 0003) — not as a second indexed collection.

## Decision / Proposal

1. **Phases 1–2 are Russian-only.** Phase 1 manifests and cleans only the 22 EPUB volumes; Phase 2 chunks, embeds (one multilingual model), and upserts only `tolstoy-ru`. No Gutenberg download script, no `tolstoy-en`, no `all-MiniLM-L6-v2` in the v1 path.
2. **English corpus deferred to Phase 6 (optional).** Gutenberg EN texts return only as an opt-in comparison collection (`tolstoy-en`, MiniLM) for cross-translation experiments — never as a default retrieval source. Phase 6 decides whether it is worth building at all.
3. **Bilingual chat is unaffected.** `lang=en` still works from day one via cross-lingual prompting (EN question → RU chunks → EN answer, RU citations). It needs only the multilingual embedder + a RU-capable generator, not an EN collection.
4. **Contracts frozen for v1.** `POST /search` and `POST /chat` accept a `collection` parameter but default to and (in v1) only serve `tolstoy-ru`. Requests for `tolstoy-en` return a clear "not built yet" response rather than silent fallback.

## Alternatives

- **Build both collections in Phase 2 as originally planned** — rejected: doubles ingest/embed work, splits focus, and the EN texts are not even downloaded while the RU set is already local.
- **Drop English entirely forever** — rejected: keeping the deferred EN table as a Phase 6 option preserves the comparison experiment without costing v1 velocity.
- **Machine-translate RU chunks into an EN collection** — rejected for v1: adds a translation pipeline with its own quality questions; generator-side translation (0003) covers the EN use case with zero extra storage.

## Consequences

- Simpler v1: one collection, one embedding model, one manifest schema (per-volume RU fields only). Stable docs (vision, architecture, stack-decision, data-sources, roadmap) must mark every `tolstoy-en` / MiniLM / Gutenberg reference as deferred.
- 0003 stays valid but its `tolstoy-en` clauses become Phase 6 options, not Phase 2 deliverables.
- Phase 6 gains an explicit opt-in decision: build `tolstoy-en` for comparison or close as RU-only.

## Open questions

1. Does Phase 6 even need `tolstoy-en`, or is generator translation sufficient permanently? (Owner: Phase 6 review.)
2. If built later, does `tolstoy-en` reuse the manifest/chunk-ID scheme from 0002 or get its own? (Owner: Phase 6 spike.)
