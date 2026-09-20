# Roadmap

Phased so each step teaches one idea and ends with something runnable. No code exists yet — phases are the build order when scaffolding starts.

## Phase 0 — Dev environment
- Python venv + Node workspace, Ollama installed, `.env.example`, lint/test wired.
- Exit: `health` check passes; models downloadable.
- Learns: repo layout, tool boundaries (Python = brain, Node = mouth).

 ## Phase 1 — Corpus (Russian-only)
  - Manifest and clean only the 22 local Russian EPUB volumes (volume → works → chapters, OPF spine order, `kind: work` vs `editorial`). No Gutenberg downloads in this phase (EN deferred — see `design-docs/0004`).
  - Cleaning to `data/clean/` with chapter detection (EPUB-aware: spine order, markup/footnotes stripped, Cyrillic punctuation kept; contract: `design-docs/0002`).
  - Exit: manifest has SHA + byte size + work list per volume; word counts logged.
  - Learns: provenance, public-domain hygiene, text normalization.

  ## Phase 2 — Baseline retrieval, Russian-only (no LLM, no English texts)
  - Chunk → embed → Chroma upsert into a single collection: `tolstoy-ru` with one multilingual embedder (all 22 vols). No `tolstoy-en`, no English embedding model in this phase.
  - `/search` endpoint + REPL: ask → see top-k chunks with scores. Verify EN queries retrieve relevant RU chunks (cross-lingual baseline for bilingual chat — needs no EN corpus).
  - Exit: "Что Толстой говорит о смерти?" returns relevant Ivan Ilyich / War and Peace chunks from `tolstoy-ru`; same question in English retrieves the same RU chunks.
  - Learns: chunk size/overlap tradeoffs, embedding comparability, cosine intuition.

 ## Phase 3 — Naive chat (first chain)
 - `naive` chain: retrieve top-4 from `tolstoy-ru` → stuff → RU-capable `llama3.2:1b`-class model via Ollama → answer + citations. `POST /chat` takes `{ question, lang }`; `lang=en` renders the same RU-grounded answer in English with RU citations (contract: `design-docs/0003`).
 - Node CLI chat client against `/chat` with `--lang ru|en` (default `ru`).
 - Exit: end-to-end conversation in Russian plus translated English session, both with visible Russian sources.
 - Learns: prompt stuffing, context limits of tiny models, grounding.

 ## Phase 4 — Chains zoo + persona
 - Add `persona` (Tolstoy voice, RU + translated EN) and `cite-or-refuse` chains; compare side by side on a fixed bilingual question set.
 - Exit: same 10 questions (RU + EN versions) answered by 3 chains, notes on style vs. faithfulness, translation fidelity checked against RU sources.
 - Learns: system prompts, temperature, refusal behavior.

 ## Phase 5 — Quality (rerank, multi-query)
 - `rerank` (12→4) and `multi-query` chains; tiny bilingual eval set (~20 Q/A in RU + EN with expected source work in the Russian volumes; EN answers must cite the same RU chunks).
 - Exit: retrieval hit-rate measured per chain (including EN-query→RU-chunk recall); winner documented.
 - Learns: recall vs. precision, eval design, when complexity pays.

  ## Phase 6 — Share & extend (+ optional English corpus)
  - Short demo notes, sample transcripts (RU + EN sessions), decision: web UI or LangChain migration.
  - Optional (and only here): build the deferred `tolstoy-en` Gutenberg collection for comparison experiments (decision: `design-docs/0004`). Not a default — v1 ships RU-only.
  - Exit: README demo section + lessons-learned note.
  - Learns: what to keep hand-rolled vs. framework.

 ## Question bank (seed for eval, bilingual — each asked in RU default + EN translation)
 1. Что Толстой думает о честолюбии? / What does Tolstoy think of ambition?
 2. Как он описывает смерть? / How does he describe death?
 3. Что такое хороший брак в его произведениях? / What is a good marriage in his works?
 4. Какую роль играют крестьяне? / What role do peasants play?
 5. Что такое счастье? / What is happiness?
 6. Как война меняет людей? / How does war change men?
 (Each should map to ≥1 known passage in the Russian volumes — the eval answers "did we retrieve it?" in both languages, citing the same RU chunks.)
