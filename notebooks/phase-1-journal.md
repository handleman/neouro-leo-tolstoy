# Phase 1 journal — corpus ingest (Russian-only)

Date: 2026-09-20. Plan: `docs/design-docs/0007-phase-1-corpus-ingest.md`.

## Result

`python -m tolstoy.manifest build` → 22 volumes, 2,430,097 work words,
`verify` OK. Spot mapping correct: vol 4 = «Война и мир», vol 8 =
«Анна Каренина», vol 13 = «Воскресение», vols 21–22 = diaries.
No volume came back empty; diary volumes (varied headings) detected fine.

## What worked

- OPF spine order via ebooklib; Vol-1-first validation caught the real
  structures (title pages, «От издательства», «Комментарии» back matter,
  numbered note bodies) before the full run.
- kind=work/editorial split behaves: Vol 1 → 114 work sections,
  223 note sidecars, 9 editorial sections (publisher essay + back matter).
- Rebuild payload deterministic (volumes[] equal across runs; only
  `generated_at` differs — byte-identity impossible by design, noted).

## What failed / needed fixing

- ebooklib 0.20 API differs from memory: no `ITEM_DOCUMENT`, items expose
  `media_type` attribute (not `get_media_type()`); synthetic test EPUB
  needs explicit `EpubNcx` + `EpubNav` or `read_epub` crashes. Fixed.
- First `normalize_text` dropped all blank lines, destroying paragraph
  boundaries the chunker needs — rewrote to split on blank runs and join
  with exactly one blank line.
- Editorial sections initially inherited stale work/chapter from the
  tracker (back matter labeled «Незаконченное/Святочная ночь»); now emit
  empty work/chapter when kind=editorial.
- Non-breaking spaces in diary headings (`1879 г.`) — collapsed at
  extraction; journal notes it as a heading-hygiene rule.
- Two self-inflicted wounds: typo'd path created a stray
  `neanou-leo-tolstoy/` dir (removed), and a tautological test assertion
  (fixed before green).

## Open for Phase 2

- 0002 Q2 (footnote sidecar link schema) still open — sidecars carry
  spine_index + head only.
- «Предисловие» deliberately NOT in editorial patterns (may be Tolstoy's
  own preface) — revisit if a volume shows publisher prefaces leaking
  into `work`.
- `data/manifest.json` built but NOT committed yet — commit with the
  Phase 1 code review.
