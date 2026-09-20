# 0003: Russian-primary corpus with on-demand English translation in chat

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

 ## Context

 The corpus is Russian-only in v1: 22 EPUB volumes in `data/raw/` (`tolstoy-ru`). English Gutenberg translations are deferred to Phase 6 as an optional comparison collection (see `0004-defer-english-corpus.md`) and are NOT built in Phases 1–2. Chat must therefore answer in Russian by default and translate to English on request without any English corpus. No doc currently defines: which collection is queried when, which embedding model serves which language, where translation happens, or what citations point to after translation.

Constraints: local-first, CPU-friendly, tiny generator via Ollama; EN/RU vectors must never mix in one collection; every answer must cite retrievable chunks; docs stay code-free.

## Decision / Proposal

 1. **Language policy** — Default chat language is Russian. The client sends `lang: ru | en` (default `ru`) with every `/chat` request; `ru` answers in Russian, `en` answers in English but always retrieves from the Russian collection.
 2. **Collections** — `tolstoy-ru` (sole v1 collection): all 22 EPUB volumes, multilingual embedding model, chunk metadata `volume, work, chapter, kind`. `tolstoy-en` (Gutenberg EN texts, English embedding model) is deferred to Phase 6 and does not exist in v1. No cross-collection vector comparison, ever.
 3. **Retrieval rule** — Both `lang=ru` and `lang=en` retrieve from `tolstoy-ru` (the authoritative text). A `tolstoy-en` opt-in (`collection: tolstoy-en`) or cross-lingual comparison chain becomes possible only if Phase 6 builds it. Rationale: translation quality is judged against one source of truth, not against two different translations.
4. **Query handling** — An English question with `lang=en` is passed to the generator alongside the Russian passages (cross-lingual prompting: the model reads RU context, writes EN answer). No separate query-translation step in v1; the embedding of the question uses the `tolstoy-ru` collection's multilingual model, which handles EN queries against RU vectors adequately for a baseline. A query-translation pre-step is deferred to the multi-query chain.
 5. **Generation contract** — `ask(question, lang) → { answer, sources[], answer_lang }`. System prompt per lang: `ru` → answer as Tolstoy in Russian, cite `Том/произведение/глава`; `en` → answer in English in Tolstoy's voice, state it is a translation of the cited Russian passages, quote short RU fragments with EN rendering. Citations always reference the Russian chunks (volume/work/chapter/chunk_id).
6. **Generator requirement** — The Ollama model must be competent in Russian (reads RU context fluently) and able to render English. Model shortlist prefers RU-capable small models; `tinyllama` is demoted to fallback because of weak Russian. Temperature stays low (~0.3) so translation stays faithful.
7. **Interface** — `POST /chat` accepts `{ question, lang, chain, collection? }`; `POST /search` accepts `{ query, collection, top_k, filter }` with collection defaulting to `tolstoy-ru`. Node CLI exposes `--lang en|ru` (or `/en` command) and renders `answer_lang` + Russian sources under translated answers.

## Alternatives

- **Translate-then-retrieve (EN query → RU translation → RU retrieval)** — more moving parts for v1; deferred. Multilingual embeddings make it unnecessary for the baseline.
 - **Retrieve from `tolstoy-en` for EN answers** — rejected as default: EN translations (Maude/Garnett) differ in vocabulary and coverage from the 22-vol Russian set; citing them would split the source of truth. Deferred with the EN corpus to Phase 6 (see 0004).
- **Separate MT model (e.g. dedicated translator) instead of generator translation** — better fidelity, but adds a second model to Phase 0. Deferred to Phase 5; generator translation is sufficient while answers are short and cited.
- **English-first with Russian as stretch goal** — rejected: contradicts repo reality (22 RU vols present, EN not yet downloaded).

## Consequences

 - Phase 2 wires a single embedding model (multilingual, RU) and a single collection (`tolstoy-ru`); the two-model/two-collection plan is deferred with the EN corpus to Phase 6 (see 0004).
 - Eval set becomes bilingual: each seed question exists in RU + EN, with expected source in the Russian volumes (EN answer must cite the same RU chunks).
- Generator choice is constrained to RU-capable models; this narrows the Ollama shortlist and must be reflected in stack-decision.
- CLI gains a language switch; transcripts in Phase 6 should show both RU and EN sessions.

## Open questions

1. Cross-lingual retrieval quality: does the chosen multilingual embedder rank RU chunks well for EN queries, or is a query-translation pre-step needed sooner? (Owner: Phase 2 eval.)
2. Which RU-capable Ollama model at ~1–3B is the v1 default? Candidates need a quick RU fluency smoke test. (Owner: Phase 0.)
3. Should `lang=en` also return the original Russian answer alongside the translation for learning purposes? (Owner: CLI UX decision, Phase 3.)
