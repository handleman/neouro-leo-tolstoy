# Data sources

All corpus texts must be public domain.

> Local find: `data/raw/` already holds a 22-volume Russian edition (EPUB, gitignored). That becomes the primary corpus; English Gutenberg translations stay as a secondary collection for comparison and faster iteration in English.

## Primary corpus (Russian, local EPUBs)

- Location: `data/raw/Толстой Л.Н-Том N..epub`, 22 volumes (already present, gitignored via `data/raw/`).
- Pipeline must handle EPUB (not just `.txt`): extract chapters, strip markup/footnotes, keep volume + work + chapter metadata per chunk.
- Embedding model for Russian must be multilingual (e.g. `paraphrase-multilingual-MiniLM-L12-v2`), separate collection (`tolstoy-ru`) so English and Russian vectors never mix.
- Manifest still required: per-volume title list, page/byte counts, SHA, source/provenance note.

## Secondary corpus (English, Gutenberg)

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
  manifest.json        # title, translator, source_url, gutenberg_id, sha256, license
  raw/                 # original EPUB/TXT files, gitignored (large)
  clean/               # stripped markup/boilerplate, gitignored (regenerable)
```

Only the manifest is committed; raw/clean are regenerable via the download script.

## Cleaning rules

1. Strip Project Gutenberg header (`*** START OF ... ***`) and footer (`*** END OF ... ***`).
2. Normalize line endings + collapse 3+ blank lines to 2.
3. Preserve chapter headings (e.g. `CHAPTER`, `BOOK`, Roman numerals) — they become `chapter` metadata on chunks.
4. Record translator name per file — translations differ in vocabulary, which matters for a "vocabulary" project.

## Licensing

Tolstoy died 1910; works are public domain. Maude (†1949) and Garnett (†1946) translations are public domain in most jurisdictions including the US. Rules:
- Only ingest texts explicitly marked public domain / no-renewal on Gutenberg.
- Never add modern translations (Pevear/Volokhonsky, Schwartz, etc.).
- Keep `license: public-domain` + source URL in the manifest per file.
- For the local Russian EPUBs: record edition/provenance in the manifest before indexing (publisher, year if known); treat as public-domain text, keep the raw files gitignored.
