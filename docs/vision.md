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
5. **Learning artifact:** notes on what worked, what failed, and why — the real output of the project.

## What success looks like

A local chat session like:

> **You:** What do you think of ambition?
> **Cyber-Tolstoy:** Ambition is the vanity of men who have forgotten the field before them... [cites: *Anna Karenina*, Part 3, chunk 412; *War and Peace*, Epilogue, chunk 88]

Criteria: answer is stylistically Tolstoyan, semantically grounded, and every claim traces to a retrievable chunk.

## Non-goals (for now)

- No production hosting, auth, or scaling.
- No fine-tuning of the base model (prompt + retrieval only at first).
- Russian-first corpus: the 22-volume local EPUB set is primary (`tolstoy-ru`); English Gutenberg translations are secondary (`tolstoy-en`) for comparison.
- No copyrighted translations (e.g. modern Pevear/Volokhonsky) — public domain only.

## Why Tolstoy?

- Large, thematically coherent corpus (war, death, faith, family, work) — great for semantic search.
- Distinctive voice — easy to judge style success/failure.
- Fully public domain — no licensing friction for a learning project.
