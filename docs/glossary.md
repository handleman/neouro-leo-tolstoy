# Glossary

Plain-language RAG vocabulary for this project. One paragraph each — depth comes from building.

- **Corpus** — the full set of Tolstoy texts we index. Versioned via manifest (what + where from).
- **Chunk** — a slice of text (~900 chars) small enough to embed and fit in a prompt. Unit of retrieval and citation.
- **Embedding** — a vector (list of numbers) representing a chunk's meaning. Similar meanings → nearby vectors.
- **Vector DB (Chroma)** — a store optimized for "find vectors near this one" (cosine similarity). Our project's memory.
- **Retriever** — embed(question) → top-k chunks. Tunables: k, score threshold, metadata filters (by work/chapter).
- **Prompt stuffing** — pasting retrieved chunks into the LLM prompt as context. Simple, effective, limited by context window.
- **System prompt / persona** — instructions shaping voice ("answer as Tolstoy, moralizing, concrete images of country life..."). Style lives here in v1, not in fine-tuning.
- **Chain** — a named pipeline: retriever settings + prompt template + model + rules. e.g. `naive`, `persona`, `cite-or-refuse`. Comparable because inputs/outputs match.
- **Rerank** — retrieve broadly (12), then keep the best 4 with a stronger scorer. Improves precision at extra cost.
- **Hallucination** — fluent answer with no basis in retrieved chunks. `cite-or-refuse` exists to punish it.
- **Eval set** — fixed questions with known-good source passages. Measures whether changes help or just feel different.
- **Ollama** — local runner for open LLMs. Lets a 1B model answer using our context instead of its (weak) parametric memory.
