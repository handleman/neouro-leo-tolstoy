# Demo transcript — RU session on the winning chain

Date: 2026-09-26. Chain: `rerank` (Phase 5 winner, 0.55 hit-rate).
Generator: `llama3.2:1b` (temperature 0.3). Store: 26,188-chunk `.chroma/`
(`tolstoy-ru`), rerank broad-12 via
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, final-4.
API: `uvicorn tolstoy.api.app:app` on :8000. CLI: `npm run chat --silent --
--lang ru --chain rerank` (piped stdin; `>` is the CLI prompt, questions are
shown as `Q:` curator labels — answers and sources are verbatim CLI output,
single representative session, not cherry-picked per answer).

```
cyber-tolstoy chat -> http://127.0.0.1:8000 [lang=ru chain=rerank]
Commands: /ru /en /chain <name> /quit
```

**Q1:** Что такое искусство?

```
> Искусство – это архитектура, ваяние, живопись, музыка, поэзия во всех ее видах.
[1] vol15 | Что такое искусство? | II | ru-vol15-что-такое-искусство-10-3 | 0.8435
[2] vol15 | Что такое искусство? | V | ru-vol15-что-такое-искусство-13-0 | 0.7819
[3] vol15 | Незаконченное, наброски | О том, что называют искусством | ru-vol15-незаконченное-наброски-63-7 | 0.8175
[4] vol15 | Незаконченное, наброски | О том, что называют искусством | ru-vol15-незаконченное-наброски-62-9 | 0.8199
```

**Q2:** Как Хаджи-Мурат встречает опасность?

```
Хаджи-Мурат встречает опасность, когда он принимает кунака Садо и подвергается угрозе от лазутчиков. Это связано с тем, что Шамиль объявил об этом жителям Чечни, под угрозой казни не принимать Хаджи-Мурата, и это привело к тому, что жители аула могут узнать о присутствии Xadhi-Murat в его доме.
[1] vol14 | Хаджи-Мурат | I | ru-vol14-хаджи-мурат-8-20 | 0.6852
[2] vol14 | Хаджи-Мурат | I | ru-vol14-хаджи-мурат-8-19 | 0.5939
[3] vol14 | Хаджи-Мурат | XXII | ru-vol14-хаджи-мурат-29-8 | 0.6049
[4] vol14 | Хаджи-Мурат | XIV | ru-vol14-хаджи-мурат-21-5 | 0.5630
```

**Q3:** Как отец Сергий борется с искушением?

```
Ответ: Отец Sergius борается с искушением, подвергаясьColdному осуждению и сознательно вызываемому замиранию мыслей и чувств.
[1] vol12 | Отец Сергий | III | ru-vol12-отец-сергий-111-13 | 0.6400
[2] vol12 | Отец Сергий | VI | ru-vol12-отец-сергий-114-3 | 0.6244
[3] vol12 | Отец Сергий | VII | ru-vol12-отец-сергий-115-10 | 0.6057
[4] vol12 | Отец Сергий | VII | ru-vol12-отец-сергий-115-0 | 0.5865
```

**Refusal demo** (same session, switched to `cite-or-refuse` — the winning
`rerank` chain has no score gate by design, so refusal is shown on the
gate chain and labeled as such):

```
chain=cite-or-refuse
Не нашёл ответа на этот вопрос в моих произведениях.
(no sources)
```

Input was gibberish (`абракадабра квантовая xyz`), refused with no generator
call. Exit: clean, no stack trace.

Curator notes: Q1 is the title-match ceiling (vol15 rank 1 at 0.84). Q2/Q3
retrieve the right works with code-switching artifacts typical of the 1b
generator (`Xadhi-Murat`, `Sergius`, `Cold` — see lessons note 0013). Source
display order is cross-encoder order, not cosine order (e.g. Q1 [3] 0.8175
above [2] 0.7819) — the shown scores are cosine, the ranking is CE.
