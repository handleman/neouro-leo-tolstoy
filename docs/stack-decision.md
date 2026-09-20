# Stack decision

Decided by maintainer; open to revision as we learn. Principles: local-first, free, CPU-friendly, explainable, both Python and Node get a real job.

## Python core (RAG, data, API)

| Choice | What | Why |
|---|---|---|
| Python 3.11+ | RAG core language | Embeddings, vector DB clients, and ML tooling live here |
| ChromaDB (persistent, local) | Vector DB | Zero-ops file-backed store, perfect for learning; no Docker needed for v1 |
| sentence-transformers `all-MiniLM-L6-v2` | Embedding model (English) | Tiny (~80MB), fast on CPU, good baseline; one model for corpus + queries |
| sentence-transformers multilingual (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) | Embedding model (Russian) | Separate model + separate collection so EN/RU vectors never mix |
| Ollama + `tinyllama` / `llama3.2:1b` / `phi3:mini` | Generator | Local tiny chat models; swap via one env var; no API keys |
| FastAPI + Uvicorn | Server | Thin HTTP boundary (`/health`, `/search`, `/chat`) so Node never imports ML code |
| pytest + ruff | Test + lint | Minimal hygiene from day one |

Managed with `pyproject.toml` (pip or uv — either works). Virtualenv at `.venv/`, vector data at `.chroma/` (both gitignored).

## Node surface (chat UX)

| Choice | What | Why |
|---|---|---|
| Node 20+ + TypeScript | Chat client language | Gives Node a genuine role without duplicating ML logic |
| `tsx` + `readline` + `fetch` | CLI chat | Zero-framework REPL that POSTs to FastAPI; later upgradable to a web UI |
| npm workspaces (`web/`) | Packaging | Keeps Node deps isolated from Python |

Node never embeds or retrieves — it only renders answers + citations.

## Alternatives considered (and deferred)

- **pgvector / Qdrant / Pinecone** — more production-like, but heavier ops or hosted keys. Revisit if Chroma limits appear. Abstraction (a `Store` interface) keeps this swap cheap.
- **LangChain / LlamaIndex** — great later for the chains zoo, but v1 is hand-rolled so each RAG step is visible and learnable. Adopt once naive RAG works.
- **OpenAI / hosted embeddings** — better quality, but costs money and hides mechanics. Local-first keeps the project reproducible for free.
- **Fine-tuning** — out of scope until RAG + prompting plateau. Retrieval gives knowledge; fine-tune would give style, but prompting gets us 80% for study purposes.

## Defaults to start with

- Chunk: ~900 chars / ~150 overlap
- Retrieve: top-k = 4 (naive), 12→4 (rerank later)
- Embeddings: `all-MiniLM-L6-v2` (EN), multilingual MiniLM (RU)
- Chat model: `llama3.2:1b` (fallback `tinyllama`), temperature low (~0.3) for groundedness
- Collections: `tolstoy-ru` (primary), `tolstoy-en` (secondary)
