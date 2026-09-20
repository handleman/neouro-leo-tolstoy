# 0001: Docs review — initial pass

- Status: Approved with comments
- Date: 2026-09-20
- Author: software-architect skill

## Context

First review of `docs/` root (vision, architecture, stack-decision, data-sources, roadmap, glossary) after the discovery that `data/raw/` already holds 22 Russian EPUB volumes (gitignored). Docs were originally written English-Gutenberg-first; data-sources was patched for Russian-primary but the rest was not.

## Findings

### Must-fix

1. `vision.md` Non-goals says "No Russian-first corpus yet — start with English" — directly contradicts repo reality (22 Russian volumes, primary corpus). Fix wording.
2. `architecture.md` diagram label "Castro? No — Cyber-Tolstoy chain" — leftover joke, unprofessional in a design doc. Fix.
3. `architecture.md` §1 + §3 describe txt-only Gutenberg ingest and "one collection (`tolstoy-en`), Russian later" — contradicts data-sources (EPUB pipeline, `tolstoy-ru` primary). Fix to two collections, EPUB-aware ingest.
4. `data-sources.md` heading "Primary corpus (Russian, local)" sits above the English Gutenberg table — mislabeled sections. Swap headings.

### Should-fix

5. `stack-decision.md` names only `all-MiniLM-L6-v2` and defaults to collection `tolstoy-en`. Add the multilingual embedding model + `tolstoy-ru` to the defaults.
6. `roadmap.md` Phase 1/2/6 are English-first (Gutenberg download, MiniLM, "decision: Russian corpus" in Phase 6). Reorder: Phase 1 manifests the local EPUBs first, Phase 6 drops the Russian-corpus decision (already made).

### Nit

7. Chunk size "~800–1000" (architecture) vs "~900" (stack-decision) — compatible ranges, no change needed. Canonical: ~900/150 per stack-decision.
8. `data-sources.md` storage layout says `raw/` holds ".txt downloads" — it holds EPUBs. Fix wording.

## Verdict

**Approve-with-comments.** Must-fix items 1–4 + nit 8 applied inline with this review; items 5–6 applied inline as well (small). No open questions beyond Phase 0 scaffolding order (EPUB parsing lands in Phase 1).
