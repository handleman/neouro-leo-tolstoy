# neouro-leo-tolstoy

Self-educational RAG project: a vector database of Leo Tolstoy's works wired to a tiny talkative model, so you can chat with a "cyber Tolstoy" in his vocabulary.

> Status: Phase 1 implemented (22-vol RU corpus ingested, `data/manifest.json` built, 2.43M work words). Build follows `docs/design-docs/0005` → `0012` in order.

## What is this?

1. Build a clean, citable corpus of Tolstoy (open sources, public domain).
2. Index it into a local vector DB (chunk → embed → store).
3. Connect a small local LLM via Retrieval-Augmented Generation (RAG).
4. Experiment with **model chains** — different retrieve → rerank → prompt → generate pipelines — and compare them.

The point is learning RAG end-to-end, not serving production traffic.

## Docs

- [Vision](docs/vision.md) — why, what success looks like, example dialogues
- [Architecture](docs/architecture.md) — how RAG + chains fit together
- [Stack decision](docs/stack-decision.md) — Python + Node, Chroma, Ollama, why
- [Data sources](docs/data-sources.md) — which Tolstoy texts, where from, licensing
- [Roadmap](docs/roadmap.md) — phased learning plan, 0 → 6
- [Glossary](docs/glossary.md) — RAG terms in plain language

## Principle

Local-first, free, explainable. Every answer should cite the passages it came from. Every chain should be swappable and comparable.

## Next step

 Read the docs in order above, then build per `docs/design-docs/0005-implementation-plan-overview.md` (Phases 0–1 done — next: Phase 2 baseline retrieval).
