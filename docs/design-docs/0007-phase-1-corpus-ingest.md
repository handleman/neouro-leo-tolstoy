# 0007: Phase 1 — corpus ingest, Russian-only (exact steps)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

Entry: Phase 0 exit (package, config, proven model ids). The 22 EPUB volumes sit in `data/raw/` (gitignored, ~25 MB, FB2-converted EPUB 2.0, OPF at `OEBPS/content.opf`). Full contract in 0002. Phase 1 produces the only versioned data artifact (`data/manifest.json`) plus regenerable `data/clean/`. No embeddings, no Chroma, no English texts (deferred per 0004).

## Decision / Proposal

Build in this exact order.

### Step 1 — EPUB reader `tolstoy/ingest/epub.py`

- Parse `OEBPS/content.opf`: read metadata (`dc:title`, `dc:creator`, `dc:language`, `dc:publisher`, `dc:date`) and manifest + spine; iterate spine items in spine order (never glob/filename order).
- Per spine item: parse XHTML, extract heading text (`h1/h2/h3`) and paragraph text (`p`); inline emphasis becomes plain text; drop cover, title page, CSS/fonts/images references, annotation boilerplate.
- Extract footnotes/endnotes to sidecar records `{ spine_index, note_id, text }` (stored, never inlined into prose).
- Output per volume: ordered section list `{ spine_index, href, headings, kind_hint, paragraphs[], footnotes[] }`. Pure function of the EPUB bytes; no I/O besides reading the file.

### Step 2 — Cleaner `tolstoy/ingest/clean.py`

- Normalize whitespace, collapse 3+ blank lines to 2, join FB2 hyphenation artifacts, deduplicate drop-cap span text, keep Cyrillic punctuation (`—`, `«»`) verbatim.
- Work/chapter detection: heading hierarchy maps to `{ work, chapter }`; sections without headings inherit the last seen heading.
- `kind` classification: `editorial` for publisher/editor front matter (`От издательства`, edition notes, converter credits) vs `work` for Tolstoy's text. Rule list lives in this module and is unit-tested per pattern.
- Output per volume `data/clean/vol{NN:02d}.json`: array of `{ spine_index, href, work, chapter, kind, text }` plus volume header (title, creator, publisher, year). `data/clean/` is gitignored and fully regenerable.

### Step 3 — Manifest builder `tolstoy/ingest/manifest.py` + CLI `python -m tolstoy.manifest`

- Per volume record: `volume, filename, title, creator, publisher, pub_year, language ("ru"), sha256, byte_size, section_count, work_list[], word_count, license ("public-domain"), source_note ("local 22-vol edition")`.
- Commands: `build` (scan `data/raw/`, clean all, write `data/manifest.json`), `verify` (re-hash raws, compare SHAs, report drift). Top-level manifest adds `generated_at` and `tool_versions`.
- `data/manifest.json` is committed; raw/clean never are.

### Step 4 — Thin CLIs + volume-1-first validation

- `python -m tolstoy.clean` (clean one `--volume` or `--all`), `python -m tolstoy.manifest build|verify`.
- Validate the whole pipeline on Volume 1 first (known structure: `Детство/Отрочество/Юность`, `От издательства` editorial), eyeball heading mapping and editorial tagging, then run all 22.

### Tests (new files in `tests/`, fixtures from Volume 1)

- `test_epub.py` — spine order matches OPF (not filename order); headings/paragraphs extracted; footnotes separated, not inlined; images/fonts ignored.
- `test_clean.py` — each editorial pattern → `kind: editorial`; Tolstoy sections → `kind: work`; heading inheritance; Cyrillic punctuation preserved.
- `test_manifest.py` — `build` then `verify` passes; tampered file fails `verify`; re-run is byte-identical (determinism).

### Exit checklist

1. `python -m tolstoy.manifest build` succeeds for all 22 volumes; `verify` passes.
2. `data/manifest.json` committed with 22 entries, each with SHA + byte size + work list + word count.
3. Word counts logged (in manifest + journal); `pytest` + `ruff` green.
4. `notebooks/phase-1-journal.md` written (heading-pattern coverage across vols, editorial edge cases).

## Alternatives

- **Convert EPUBs to TXT offline first** — rejected (0002): loses spine order and heading structure, adds a manual step, breaks provenance.
- **Embed editorial matter too** — rejected for v1 (0002): pollutes retrieval with non-Tolstoy voice; stored and tagged, excludable by filter.
- **SQLite instead of JSON for clean text** — rejected: 22 JSON files are inspectable, diffable, and tiny enough (~25 MB total); no query needs justify a DB here.

## Consequences

- Phase 2 consumes `data/clean/*.json` + manifest and needs no EPUB knowledge.
- Manifest becomes the corpus version: any raw-file change is detectable via `verify`.
- Heading-pattern gaps across volumes surface here, not during chunking.

## Open questions

1. Heading-pattern coverage on vols 2–22 (same `h2` convention as Vol. 1?) — answered by the Step 4 validation run.
2. Footnote sidecar link key (chunk ID vs spine position) — follow-up; sidecars are stored but unlinked in Phase 1.
3. `kind: editorial` opt-in `/search` filter — API decision in Phase 2 (default hidden).
