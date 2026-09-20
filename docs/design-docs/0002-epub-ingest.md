# 0002: EPUB ingest support (Russian 22-volume set)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

`data/raw/` holds 22 Russian EPUB volumes (`Толстой Л.Н-Том N..epub`, ~25 MB total, gitignored). This is the primary corpus that the vector DB and model chains learn from. Docs so far say "EPUB-aware" but define no contract: how chapters are extracted, ordered, cleaned, or turned into chunk metadata.

Inspection of Volume 1 shows the concrete structure to design against: EPUB 2.0, FB2-converted (`Fb2epub v1.1.5.0`, Sigil), OPF at `OEBPS/content.opf` with `dc:title` (volume title + series), `dc:creator` (Лев Николаевич Толстой), `dc:language ru`, `dc:publisher` (Художественная литература), `dc:date original-publication 1978`, `dc:description`; manifest of `OEBPS/Text/sectionN.xhtml` + cover/images/fonts/CSS; body content in XHTML (`h2` titles, `p` paragraphs, `em` emphasis, drop-cap spans). Spine order in the OPF defines reading order. Front matter includes editorial sections (e.g. `От издательства`) that are not Tolstoy's text.

Constraints: raw EPUBs stay gitignored and are never committed; only `data/manifest.json` is versioned; `data/clean/` is regenerable; docs stay code-free (contracts, not implementation).

## Decision / Proposal

Support EPUB as a first-class ingest source alongside Gutenberg `.txt`, with Russian EPUBs as the default path:

1. **Source handling** — Ingest reads EPUBs in OPF spine order (never filesystem/glob order). Each volume maps to one EPUB file; volume number is parsed from the filename (`Том N`) and cross-checked against the OPF `dc:title`.
2. **Extraction contract** — Per spine item, extract: heading text (`h1/h2/h3`), paragraph text (`p`), inline emphasis preserved as plain text (no markup in stored chunks). Drop: cover, title page, CSS, fonts, images, annotation boilerplate. Footnotes/endnotes are extracted to separate sidecar records, not inlined into prose chunks.
3. **Editorial filtering** — Non-authorial front/back matter (`От издательства`, publisher notes, FB2 converter credits) is cleaned to `data/clean/` but tagged `kind: editorial` and excluded from the default retrieval index. Only `kind: work` (Tolstoy's text) is embedded into `tolstoy-ru`.
4. **Work/chapter detection** — Headings become the `work` / `chapter` chunk metadata. Hierarchy: volume → work (e.g. `Детство`) → chapter/section heading. Sections without a recognizable heading inherit the last seen heading; every chunk carries `volume, work, chapter, spine_index`.
5. **Cleaning rules (EPUB)** — Normalize whitespace, collapse 3+ blank lines to 2, join hyphenated line-break artifacts from FB2 conversion, strip drop-cap span duplication, keep Cyrillic punctuation (`—`, `«»`) verbatim. Chapter headings are preserved as metadata, not deleted.
6. **Manifest fields (per EPUB)** — `volume, filename, title (OPF dc:title), creator, publisher, pub_year, language: ru, source_note (local 22-vol edition), sha256, byte_size, section_count, work_list[]`. Same manifest file also records Gutenberg EN entries with their own fields (`gutenberg_id, translator, source_url`).
7. **Idempotency** — Chunk IDs are deterministic: `ru-vol{NN}-{work-slug}-{spine_index}-{ordinal}` so re-ingest of the same file upserts without duplication. Changed SHA → new ingest run logged in manifest.
8. **Interface** — Ingest remains three pure steps (load/clean → chunk → embed/store), each testable on a single EPUB section. EPUB parsing is confined to step 1; steps 2–3 are format-agnostic.

## Alternatives

- **TXT-only + convert EPUBs offline** — rejected: loses spine order and heading structure, adds a manual step, breaks provenance.
- **Embed editorial matter too** — rejected for v1: pollutes retrieval with Soviet-editorial voice; kept on disk and tagged so it can be opted in later via metadata filter.
- **Inline footnotes into prose** — rejected: breaks Tolstoy's long-paragraph flow and inflates chunks; sidecar records allow a later `footnote` chain without touching the base index.
- **Filename order instead of spine order** — rejected: `sectionN.xhtml` numbering is not reading order across all volumes; OPF spine is the single source of truth.

## Consequences

- `tolstoy-ru` becomes the real primary collection (22 vols, full-text, citable to volume/work/chapter).
- Ingest depends on an EPUB/OPF parser (see stack-decision); Gutenberg `.txt` path is unchanged and stays as the secondary `tolstoy-en` source.
- Cleaning must be validated per volume (heading patterns vary across 22 vols); manifest generation becomes Phase 1's exit artifact.
- Chunking/embed steps need no format knowledge — they consume `data/clean/` + manifest.

## Open questions

1. Heading-pattern coverage: do all 22 volumes use the same `h2`-per-work convention as Vol. 1, or are per-volume heading rules needed? (Owner: Phase 1 spike.)
2. Footnote sidecar schema: link back to exact chunk ID or to spine position? (Owner: 0002 follow-up.)
3. Should `kind: editorial` chunks be queryable via an opt-in filter in `/search` v1, or hidden entirely? (Owner: API design.)
