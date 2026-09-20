# Vision

## Purpose

A self-education project to learn **RAG-enhanced model chains** by building one concrete thing: a cyber version of Leo Tolstoy you can talk to.

Instead of abstract tutorials, every concept (chunking, embeddings, retrieval, prompting, evaluation) is learned against a single corpus — Tolstoy's works — and a single test: *does it sound like Tolstoy, and can it prove it with citations?*

## Goals

1. **Corpus:** a versioned, clean collection of Tolstoy's works from open sources, with provenance (which edition/translation, where downloaded, public-domain status).
2. **Vector memory:** all works chunked, embedded, and searchable by meaning, stored locally.
3. **Talkative model:** a tiny local LLM (1–3B params) that answers in Tolstoy's vocabulary — moral inquiry, peasant wisdom, long reflective sentences — grounded in retrieved passages.
 4. **Chains zoo:** not one RAG pipeline but several comparable chains:
   - naive RAG (retrieve → stuff into prompt → generate)
   - RAG + rerank
   - RAG + persona / style prompt
   - RAG + cite-or-refuse (no hallucination without sources)
   - later: multi-query, HyDE, agents
 5. **Bilingual chat:** Russian is the voice of the corpus and the default answer language; English is an on-demand translation of the same Russian-grounded answer (see `design-docs/0003`). No English corpus needed — translation is rendered by the generator from Russian chunks.
 6. **Learning artifact:** notes on what worked, what failed, and why — the real output of the project.

## What success looks like

 A local chat session like:

 > **You:** Что ты думаешь о честолюбии?
 > **Cyber-Tolstoy:** Честолюбие есть суета людей, забывших о поле перед ними... [источники: *Анна Каренина*, часть 3, чанк 412; *Война и мир*, Эпилог, чанк 88]

 The same session in English (`--lang en`) retrieves the same Russian passages and renders the answer in English as a translation, still citing the Russian chunks:

 > **You:** What do you think of ambition? (`--lang en`)
 > **Cyber-Tolstoy (translated from RU sources):** Ambition is the vanity of men who have forgotten the field before them... [sources: *Anna Karenina*, Part 3, chunk 412 (RU); *War and Peace*, Epilogue, chunk 88 (RU)]

 Criteria: answer is stylistically Tolstoyan, semantically grounded, cites retrievable chunks (Russian chunks even for English answers), and states when it is a translation.

## Non-goals (for now)

 - No production hosting, auth, or scaling.
 - No fine-tuning of the base model (prompt + retrieval only at first).
 - Russian-only corpus in v1: the 22-volume local EPUB set (`tolstoy-ru`). English Gutenberg translations are deferred to Phase 6 as an optional comparison collection (see `design-docs/0004`) — not built in Phases 1–2. Chat answers in Russian by default with on-demand English translation of the Russian-grounded answer — never English-first retrieval.
 - No copyrighted translations (e.g. modern Pevear/Volokhonsky) — public domain only.

## Why Tolstoy?

- Large, thematically coherent corpus (war, death, faith, family, work) — great for semantic search.
- Distinctive voice — easy to judge style success/failure.
- Fully public domain — no licensing friction for a learning project.
