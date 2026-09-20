# Data sources

All corpus texts must be public domain.

 > Local find: `data/raw/` already holds a 22-volume Russian edition (EPUB, gitignored). That is the sole v1 corpus. English Gutenberg translations are deferred to Phase 6 as an optional comparison collection (see `design-docs/0004`) — not downloaded or indexed in Phases 1–2.

 ## Primary corpus (Russian, local EPUBs)

 - Location: `data/raw/Толстой Л.Н-Том N..epub`, 22 volumes (~25 MB total, already present, gitignored via `data/raw/` — never committed; model and vector DB learn from these files locally).
 - Format (verified Vol. 1, assumed all): EPUB 2.0, FB2-converted (`Fb2epub`, Sigil), OPF at `OEBPS/content.opf`, content in `OEBPS/Text/sectionN.xhtml` (XHTML: `h2` titles, `p` paragraphs, drop-cap spans, `em`). OPF metadata observed: `dc:title` (volume + series `Собрание сочинений в двадцати двух томах`), `dc:creator` (Лев Николаевич Толстой), `dc:language ru`, `dc:publisher` (Художественная литература), `dc:date original-publication 1978`.
 - Pipeline must handle EPUB (not just `.txt`): read OPF spine order (not filename order), extract headings/paragraphs, strip markup/images/fonts, separate footnotes to sidecars, tag editorial matter (`От издательства`, converter credits) as `kind: editorial` (stored but excluded from retrieval) vs Tolstoy's text (`kind: work`). Full contract: `design-docs/0002-epub-ingest.md`.
 - Embedding model for Russian must be multilingual (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) in the `tolstoy-ru` collection. The same multilingual model embeds EN queries for cross-lingual retrieval of RU chunks (see `design-docs/0003`). (If Phase 6 ever builds `tolstoy-en`, it gets its own model so EN/RU vectors never mix.)
 - Manifest still required: per-volume `volume, filename, title, creator, publisher, pub_year, language, sha256, byte_size, section_count, work_list[]`, plus source/provenance note.

 ## Secondary corpus (English, Gutenberg) — DEFERRED to Phase 6

 > Not built in Phases 1–2. No downloads, no `tolstoy-en` collection, no English embedding model in v1. The table below is kept as a future reference for the optional comparison experiment (decision: `design-docs/0004`).

| Work | Gutenberg ID | URL pattern | Notes |
|---|---|---|---|
| War and Peace | 2600 | `gutenberg.org/cache/epub/2600/pg2600.txt` | Maude translation (public domain) |
| Anna Karenina | 1399 | `.../epub/1399/pg1399.txt` | Garnett translation |
| Resurrection | 1938 | `.../epub/1938/pg1938.txt` | Maude translation |
| The Kreutzer Sonata | 351 | `.../epub/351/pg351.txt` | Short — good for fast tests |
| The Death of Ivan Ilyich | 2462 | `.../epub/2462/pg2462.txt` | Short — good for fast tests |
| Childhood / Boyhood / Youth | 2142, 6999* | verify ID before ingest | Trilogy, optional v1 |
| Short stories mix | various | curated later | Start with the 5 above |

*IDs to verify at download time — Gutenberg occasionally renumbers. The download script must log the final URL + byte size + SHA per file.*

Suggested bootstrap order: Kreutzer + Ivan Ilyich first (small, fast iteration), then Anna Karenina, Resurrection, War and Peace last (largest).

 ## Storage layout (planned)

  ```text
  data/
    manifest.json        # v1: per-volume RU EPUB fields (volume, filename, title, creator, publisher, pub_year, language, sha256, byte_size, section_count, work_list[], license); Phase 6 (optional): + per-file EN TXT fields (translator, source_url, gutenberg_id)
    raw/                 # v1: 22 RU EPUBs, gitignored (large, never committed; vector DB learns from here). EN TXT downloads only if Phase 6 builds them.
    clean/               # spine-ordered plain text + heading map per volume, gitignored (regenerable)
  ```

  Only the manifest is committed; raw/clean are re-extractable from the local EPUBs (EN downloads regenerable via script only if Phase 6 proceeds).

 ## Cleaning rules

  1. EPUB: read OPF spine order; per section extract `h1/h2/h3` + `p` text, drop cover/title-page/images/CSS/fonts; footnotes to sidecars (not inlined); tag `От издательства`-style front matter as `kind: editorial` (excluded from index).
  2. TXT (Phase 6 only, if EN corpus is built): strip Project Gutenberg header (`*** START OF ... ***`) and footer (`*** END OF ... ***`).
  3. Both (when EN exists): normalize line endings + collapse 3+ blank lines to 2; join FB2 hyphenation artifacts; strip drop-cap span duplication; keep Cyrillic punctuation (`—`, `«»`) verbatim.
  4. Preserve volume/work/chapter headings — they become `volume/work/chapter/spine_index` metadata on chunks (RU; EN adds `translator` if built).
  5. Record translator/edition name per file — translations differ in vocabulary, which matters for a "vocabulary" project.

## Licensing

Tolstoy died 1910; works are public domain. Maude (†1949) and Garnett (†1946) translations are public domain in most jurisdictions including the US. Rules:
- Only ingest texts explicitly marked public domain / no-renewal on Gutenberg.
- Never add modern translations (Pevear/Volokhonsky, Schwartz, etc.).
- Keep `license: public-domain` + source URL in the manifest per file.
- For the local Russian EPUBs: record edition/provenance in the manifest before indexing (publisher, year if known); treat as public-domain text, keep the raw files gitignored.
