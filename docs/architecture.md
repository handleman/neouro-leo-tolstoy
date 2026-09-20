# Architecture

## Big picture

 ```text
  Local corpus (data/raw)           Ingest pipeline (Python)        Local memory
 ┌─────────────────────┐       ┌──────────────────────┐       ┌──────────────┐
 │ 22 Russian EPUB vols│       │ load + clean         │       │ ChromaDB     │
 │ (sole v1 corpus,    │       │  EPUB: OPF spine     │       │ tolstoy-ru   │
 │  gitignored, OPF    │──────▶│  order, XHTML → text │──────▶│ (multiling.  │
 │  spine order)       │ epub  │  editorial filtered  │  vec  │  embeddings) │
 │                     │       │ chunk (overlap)      │       │              │
 │ (EN Gutenberg .txt  │       │ embed (single model) │       │ (tolstoy-en  │
 │  deferred to Ph.6)  │       │                      │       │  deferred)   │
 └─────────────────────┘       └──────────────────────┘       └──────┬───────┘
                                                                     │ top-k
                                                                     ▼
 Cyber-Tolstoy chain (Python)                       Chat surfaces
 ┌────────────────────────────────────────────┐       ┌──────────────────────┐
 │ 1. retriever: query → top-k chunks         │       │ Python REPL / API    │
 │    (tolstoy-ru only in v1)                 │       │ Node CLI chat client │
 │ 2. prompt builder: persona + context + q   │──────▶│  (--lang ru|en,      │
 │    (+ answer_lang instruction)             │  JSON │   default ru)        │
 │ 3. generator: RU-capable local LLM via     │       │ (later: tiny web UI) │
 │    Ollama (RU answer; EN = translation)    │       │                      │
 │ 4. answer + citations (always RU chunks)   │       │                      │
 └────────────────────────────────────────────┘       └──────────────────────┘

 Contracts: `design-docs/0002-epub-ingest.md` (EPUB ingest), `design-docs/0003-russian-primary-bilingual-chat.md` (language policy), `design-docs/0004-defer-english-corpus.md` (EN deferral).
 ```

## Components

  ### 1. Corpus (`data/`)
  Local EPUB volumes (`data/raw/`, 22 vols, gitignored) — the sole v1 corpus. A manifest records per volume: title, edition, SHA hash, byte size, work list, license. (English Gutenberg `.txt` downloads are deferred to Phase 6 as an optional comparison collection; see `design-docs/0004`.) EPUB cleaning follows the spine order in `OEBPS/content.opf`, extracts XHTML paragraph text, strips markup/footnotes/images, and tags editorial front matter (`kind: editorial`, excluded from retrieval) versus Tolstoy's text (`kind: work`). Volume/work/chapter/spine markers become chunk metadata (full contract: `design-docs/0002`).

  ### 2. Ingest pipeline
  Three pure steps, each independently testable (this is the educational core):
  - **Load/clean** — EPUB: read OPF spine order, XHTML → plain text, filter `kind: editorial`; normalize whitespace, detect works/chapters. (Gutenberg TXT boilerplate-stripping deferred with the EN corpus to Phase 6.)
  - **Chunk** — ~800–1000 chars with ~150 overlap. Keeps Tolstoy's long paragraphs mostly intact. Metadata per chunk: `volume, work, chapter, spine_index, kind, chunk_id`. Chunk IDs are deterministic so re-ingest upserts idempotently.
  - **Embed/store** — a single multilingual embedding model for `tolstoy-ru` in v1. Upserts are idempotent (same text → same ID). (A second model + `tolstoy-en` collection arrive only if Phase 6 builds the EN comparison corpus; vectors never mix.)

 ### 3. Vector store
 One collection in v1: `tolstoy-ru` (multilingual embeddings over all 22 EPUB volumes). Query = embed question with the collection's model → cosine top-k, with optional filters by volume/work/chapter. (`tolstoy-en` with MiniLM is deferred to Phase 6 as an optional comparison collection and never mixed with RU vectors.)

  ### 4. Model chains
  A "chain" = retriever + prompt template + generator + post-processing. All chains share the same interface: `ask(question, lang) → { answer, sources[], answer_lang }`. In v1 retrieval is always `tolstoy-ru` for both languages (EN answers are translations of RU-grounded results). (`tolstoy-en` opt-in for comparison arrives only if Phase 6 builds it.) This lets us compare:

| Chain | Retrieve | Prompt | Notes |
|---|---|---|---|
| `naive` | top-4, no filter | stuff context | baseline |
| `persona` | top-4 | + Tolstoy voice instructions | style test |
| `cite-or-refuse` | top-4, threshold | must cite or say "not in my works" | anti-hallucination |
| `rerank` (later) | top-12 → rerank to 4 | stuff | quality test |
| `multi-query` (later) | 3 rewrites → merge | stuff | recall test |

New chains are added as config + prompt variants, not rewrites.

 ### 5. Generator
 Ollama serving a tiny RU-capable chat model locally (must read Russian fluently and render English translations). RAG does the heavy lifting (knowledge), so the model can stay small — its job is voice + reasoning over provided context, plus faithful RU→EN rendering when `lang=en`.

  ### 6. Interfaces
  - **Python** owns everything data/ML: ingest, store, chains, FastAPI (`/search`, `/chat`, `/health`). `POST /chat` accepts `{ question, lang, chain, collection? }` (`lang` defaults to `ru`, `collection` defaults to `tolstoy-ru` — the only v1 collection; `tolstoy-en` requests return "not built yet"); `POST /search` accepts `{ query, collection, top_k, filter }`.
  - **Node/TypeScript** owns the talkative surface: a CLI chat client calling the API, with `--lang ru|en` (default `ru`) and rendering of `answer_lang` plus Russian sources under translated answers. Keeps both languages in the repo with a clean boundary (HTTP/JSON), so the frontend can later become a web UI without touching RAG logic.
  - **Deploy posture:** the API is stateless (config + client handles only; all corpus state in the store backend) and every deployment-varying value comes from env — the same `/search` + `/chat` contracts serve the CLI now and a web UI or online service later with no redesign (constraints: `design-docs/0014`).

 ## Data flow (chat)

 1. User asks a question in Node CLI (with `--lang ru|en`, default `ru`).
 2. Python embeds the question with the target collection's model (default `tolstoy-ru` multilingual), retrieves top-k chunks from Chroma.
 3. Prompt builder assembles: system persona + retrieved Russian passages + question + answer-language instruction (`ru` = answer in Russian; `en` = answer in English as translation).
 4. Ollama generates; response returns answer text + `answer_lang` + chunk citations (always the Russian chunks for both languages).
 5. CLI renders answer with sources (for `en`, marked as translated from RU sources). No sources → model must say so (per chain policy).
