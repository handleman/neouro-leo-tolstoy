# Stack decision

Decided by maintainer; open to revision as we learn. Principles: local-first, free, CPU-friendly, explainable, both Python and Node get a real job.

## Python core (RAG, data, API)

| Choice | What | Why |
|---|---|---|
 | Python 3.11+ | RAG core language | Embeddings, vector DB clients, and ML tooling live here |
 | ChromaDB (persistent, local) | Vector DB | Zero-ops file-backed store, perfect for learning; no Docker needed for v1 |
  | `ebooklib` (or stdlib `zipfile` + XHTML parse) + OPF spine reader | EPUB ingest | Reads the 22-vol Russian EPUBs in OPF spine order, extracts headings/paragraphs, separates footnotes; confined to load/clean step (contract: `design-docs/0002`) |
  | sentence-transformers multilingual (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) | Embedding model (Russian, `tolstoy-ru` — sole v1 collection) | Single v1 model for corpus + queries (RU and EN queries alike); cross-lingual retrieval of RU chunks needs no second model |
  | sentence-transformers `all-MiniLM-L6-v2` | Embedding model (English, `tolstoy-en` — deferred to Phase 6) | NOT installed in Phases 1–2. Reserved for the optional EN comparison collection (see `design-docs/0004`) |
 | Ollama + RU-capable `llama3.2:1b` / `phi3:mini` class (`tinyllama` fallback only) | Generator | Local tiny chat models; swap via one env var; no API keys. Default must read Russian fluently and render EN translations (see `design-docs/0003`); `tinyllama` is fallback only due to weak Russian |
 | FastAPI + Uvicorn | Server | Thin HTTP boundary (`/health`, `/search`, `/chat` with `{ question, lang, chain, collection? }`) so Node never imports ML code |
| pytest + ruff | Test + lint | Minimal hygiene from day one |

Managed with `pyproject.toml` (pip or uv — either works). Virtualenv at `.venv/`, vector data at `.chroma/` (both gitignored).

## Node surface (chat UX)

| Choice | What | Why |
|---|---|---|
 | Node 20+ + TypeScript | Chat client language | Gives Node a genuine role without duplicating ML logic |
 | `tsx` + `readline` + `fetch` | CLI chat | Zero-framework REPL that POSTs to FastAPI with `{ question, lang }`; `--lang ru\|en` switch (default `ru`), renders `answer_lang` + RU sources; later upgradable to a web UI |
| npm workspaces (`web/`) | Packaging | Keeps Node deps isolated from Python |

Node never embeds or retrieves — it only renders answers + citations.

## Alternatives considered (and deferred)

- **pgvector / Qdrant / Pinecone** — more production-like, but heavier ops or hosted keys. Revisit if Chroma limits appear. Abstraction (a `Store` interface) keeps this swap cheap.
- **LangChain / LlamaIndex** — great later for the chains zoo, but v1 is hand-rolled so each RAG step is visible and learnable. Adopt once naive RAG works.
- **OpenAI / hosted embeddings** — better quality, but costs money and hides mechanics. Local-first keeps the project reproducible for free.
 - **Fine-tuning** — out of scope until RAG + prompting plateau. Retrieval gives knowledge; fine-tune would give style, but prompting gets us 80% for study purposes.
 - **Service deployment (hosting, auth, containers)** — not built in v1, but v1 stays deploy-compatible per `design-docs/0014` (env-only config, stateless API, `Store`/`generate` interfaces, rebuildable index). No deploy work now; no redesign later.

 ## Defaults to start with

  - Chunk: ~900 chars / ~150 overlap
  - Retrieve: top-k = 4 (naive), 12→4 (rerank later); sole v1 collection `tolstoy-ru` for both chat languages
  - Embeddings: multilingual MiniLM (`tolstoy-ru`) in v1; `all-MiniLM-L6-v2` (`tolstoy-en`) deferred to Phase 6 — never mixed
  - Chat model: RU-capable `llama3.2:1b` class (fallback `tinyllama`), temperature low (~0.3) for groundedness + faithful translation
  - Chat: `lang=ru` default, `lang=en` = translation of RU-grounded answer with RU citations
  - Collections: `tolstoy-ru` (v1); `tolstoy-en` deferred to Phase 6 (optional)
