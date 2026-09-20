# Roadmap

Phased so each step teaches one idea and ends with something runnable. No code exists yet — phases are the build order when scaffolding starts.

## Phase 0 — Dev environment
- Python venv + Node workspace, Ollama installed, `.env.example`, lint/test wired.
- Exit: `health` check passes; models downloadable.
- Learns: repo layout, tool boundaries (Python = brain, Node = mouth).

## Phase 1 — Corpus
- Manifest the 22 local Russian EPUB volumes first (volume → works → chapters), then the 5 Gutenberg English texts (short ones first).
- Cleaning to `data/clean/` with chapter detection (EPUB-aware: markup/footnotes stripped).
- Exit: manifest has URL + SHA per file; word counts logged.
- Learns: provenance, public-domain hygiene, text normalization.

## Phase 2 — Baseline retrieval (no LLM)
- Chunk → embed (`all-MiniLM-L6-v2`) → Chroma upsert.
- `/search` endpoint + REPL: ask → see top-k chunks with scores.
- Exit: "What does Tolstoy say about death?" returns relevant Ivan Ilyich / War and Peace chunks.
- Learns: chunk size/overlap tradeoffs, embedding comparability, cosine intuition.

## Phase 3 — Naive chat (first chain)
- `naive` chain: retrieve top-4 → stuff → `llama3.2:1b` via Ollama → answer + citations.
- Node CLI chat client against `/chat`.
- Exit: end-to-end conversation with visible sources.
- Learns: prompt stuffing, context limits of tiny models, grounding.

## Phase 4 — Chains zoo + persona
- Add `persona` (Tolstoy voice) and `cite-or-refuse` chains; compare side by side on a fixed question set.
- Exit: same 10 questions answered by 3 chains, notes on style vs. faithfulness.
- Learns: system prompts, temperature, refusal behavior.

## Phase 5 — Quality (rerank, multi-query)
- `rerank` (12→4) and `multi-query` chains; tiny eval set (~20 Q/A with expected source work).
- Exit: retrieval hit-rate measured per chain; winner documented.
- Learns: recall vs. precision, eval design, when complexity pays.

## Phase 6 — Share & extend
- Short demo notes, sample transcripts, decision: web UI or LangChain migration.
- Exit: README demo section + lessons-learned note.
- Learns: what to keep hand-rolled vs. framework.

## Question bank (seed for eval)
1. What does Tolstoy think of ambition?
2. How does he describe death?
3. What is a good marriage in his works?
4. What role do peasants play?
5. What is happiness?
6. How does war change men?
(Each should map to ≥1 known passage — the eval answers "did we retrieve it?")
