# Architecture

## Big picture

```text
  Local corpus (data/raw)           Ingest pipeline (Python)        Local memory
 ┌─────────────────────┐       ┌──────────────────────┐       ┌──────────────┐
 │ 22 Russian EPUB vols│       │ load + clean         │       │ ChromaDB     │
 │ Gutenberg EN .txt   │──────▶│ chunk (overlap)      │──────▶│ tolstoy-ru   │
 │ (secondary)         │ epub+ │ embed (per-lang)     │  vec  │ tolstoy-en   │
 └─────────────────────┘ txt   └──────────────────────┘       └──────┬───────┘
                                                                     │ top-k
                                                                     ▼
 Cyber-Tolstoy chain (Python)                       Chat surfaces
 ┌────────────────────────────────────────────┐       ┌──────────────────────┐
 │ 1. retriever: query → top-k chunks         │       │ Python REPL / API    │
 │ 2. prompt builder: persona + context + q   │──────▶│ Node CLI chat client │
 │ 3. generator: tiny local LLM via Ollama    │  JSON │ (later: tiny web UI) │
 │ 4. answer + citations                      │       │                      │
 └────────────────────────────────────────────┘       └──────────────────────┘
```

## Components

### 1. Corpus (`data/`)
Local EPUB volumes (`data/raw/`, 22 vols, gitignored) plus English Gutenberg `.txt` downloads. A manifest records per file: title, author, translator/edition, source URL, SHA hash, license. Cleaning strips Gutenberg boilerplate or EPUB markup/footnotes but keeps volume/work/chapter markers — they become chunk metadata.

### 2. Ingest pipeline
Three pure steps, each independently testable (this is the educational core):
- **Load/clean** — normalize whitespace, remove boilerplate, detect chapters.
- **Chunk** — ~800–1000 chars with ~150 overlap. Keeps Tolstoy's long paragraphs mostly intact. Metadata per chunk: `source, chapter, chunk_id`.
- **Embed/store** — one embedding model for the whole collection so vectors are comparable. Upserts are idempotent (same text → same ID).

### 3. Vector store
Two collections: `tolstoy-ru` (primary, multilingual embeddings) and `tolstoy-en` (secondary, MiniLM). Query = embed question with the matching collection's model → cosine top-k, with optional filters by work/chapter.

### 4. Model chains
A "chain" = retriever + prompt template + generator + post-processing. All chains share the same interface: `ask(question) → { answer, sources[] }`. This lets us compare:

| Chain | Retrieve | Prompt | Notes |
|---|---|---|---|
| `naive` | top-4, no filter | stuff context | baseline |
| `persona` | top-4 | + Tolstoy voice instructions | style test |
| `cite-or-refuse` | top-4, threshold | must cite or say "not in my works" | anti-hallucination |
| `rerank` (later) | top-12 → rerank to 4 | stuff | quality test |
| `multi-query` (later) | 3 rewrites → merge | stuff | recall test |

New chains are added as config + prompt variants, not rewrites.

### 5. Generator
Ollama serving a tiny chat model locally. RAG does the heavy lifting (knowledge), so the model can stay small — its job is voice + reasoning over provided context.

### 6. Interfaces
- **Python** owns everything data/ML: ingest, store, chains, FastAPI (`/search`, `/chat`, `/health`).
- **Node/TypeScript** owns the talkative surface: a CLI chat client calling the API. Keeps both languages in the repo with a clean boundary (HTTP/JSON), so the frontend can later become a web UI without touching RAG logic.

## Data flow (chat)

1. User asks a question in Node CLI.
2. Python embeds the question, retrieves top-k chunks from Chroma.
3. Prompt builder assembles: system persona + retrieved passages + question.
4. Ollama generates; response returns answer text + chunk citations.
5. CLI renders answer with sources. No sources → model must say so (per chain policy).
