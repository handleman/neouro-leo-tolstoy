# Demo transcript — EN session on the winning chain

Date: 2026-09-26. Chain: `rerank` (Phase 5 winner, 0.55 hit-rate).
Generator: `llama3.2:1b` (temperature 0.3). Store: 26,188-chunk `.chroma/`
(`tolstoy-ru`), rerank broad-12 via
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, final-4.
API: `uvicorn tolstoy.api.app:app` on :8000. CLI: `npm run chat --silent --
--lang en --chain rerank` (piped stdin; `>` is the CLI prompt, questions are
shown as `Q:` curator labels — answers and sources are verbatim CLI output,
single representative session, not cherry-picked per answer). Same three
questions as the RU session. `[translated from RU sources]` is the CLI's
marker for `answer_lang=en`; cited sources are the same RU chunks.

```
cyber-tolstoy chat -> http://127.0.0.1:8000 [lang=en chain=rerank]
Commands: /ru /en /chain <name> /quit
```

**Q1:** What is art?

```
> [translated from RU sources]
The answer to the question "What is art?" as translated from Russian sources:

Art is entertainment that gives people a break and relaxation. Art provides enjoyment for those who are working hard, it's about experiencing different emotional states and feelings through an activity or performance (e.g., music, dance). If everyone in society was doing this work voluntarily, there would be no need to create art.

Art is not just beautiful things that exist; rather, it's the way of expressing oneself outside of life. It can also include actions like writing poetry or playing instruments and singing songs which evoke feelings (e.g., Shakespearean plays).
[1] vol15 | Незаконченное, наброски | О том, что называют искусством | ru-vol15-незаконченное-наброски-63-7 | 0.8081
[2] vol15 | Что такое искусство? | II | ru-vol15-что-такое-искусство-10-3 | 0.8332
[3] vol15 | Что такое искусство? | V | ru-vol15-что-такое-искусство-13-0 | 0.7783
[4] vol15 | Незаконченное, наброски | О том, что называют искусством | ru-vol15-незаконченное-наброски-62-9 | 0.8136
```

**Q2:** How does Hadji-Murat face danger?

```
[translated from RU sources]
The answer is translated from Russian sources. 

Haji Murat faces danger in several ways:

1. **He risks his life by taking a guest into his home**: As soon as Eldar wants to eat with Haji Murat, but he doesn't want any food anymore and instead brings him some kumgan (a type of meat) from the table.

2.  He knows that if anyone finds out about this meeting in Chечenia, they will be killed for helping a guest.
3.  When two bandits arrive at his home with swords drawn, Haji Murat doesn't want to fight them but instead wants to protect Eldar and keep him safe from harm.

4.  He is worried that if anyone finds out about this meeting in Chечenia, they will be punished for helping a guest.
5.  When the bandits ask how he plans to deal with them after their encounter, Haji Murat tells them not to worry because "the answer will come from who gives the order."
[1] vol14 | Хаджи-Мурат | I | ru-vol14-хаджи-мурат-8-19 | 0.5482
[2] vol14 | Хаджи-Мурат | I | ru-vol14-хаджи-мурат-8-20 | 0.6610
[3] vol14 | Хаджи-Мурат | XXII | ru-vol14-хаджи-мурат-29-8 | 0.5625
[4] vol14 | Хаджи-Мурат | VI | ru-vol14-хаджи-мурат-13-6 | 0.5223
```

**Q3:** How does Father Sergius struggle with temptation?

```
[translated from RU sources]
Translated from Russian sources:

The excerpts suggest that the father's struggles are rooted in his desire to protect and guide others. He is described as a man who has been blessed by God (as seen in the story of Nikodim) but still grapples with the challenges of life, particularly when it comes to spiritual matters.

Father Sergius appears to be struggling with temptation because he feels responsible for guiding his family members towards righteousness and away from sin. He is aware that they are not yet mature enough or strong-willed to handle difficult situations on their own, so he must intervene and offer guidance (as seen in the story of Nikodim).

The father's struggles also seem to be driven by a sense of duty and obligation to his family members. He feels a deep connection with them and wants to protect and care for them, which can lead him into temptation.

In general, Father Sergius appears to struggle with feelings of inadequacy and the desire to please others, particularly those in positions of authority or influence (as seen in his interactions with Anna Karenina).
[1] vol12 | Отец Сергий | III | ru-vol12-отец-сергий-111-13 | 0.6548
[2] vol12 | Отец Сергий | VI | ru-vol12-отец-сергий-114-3 | 0.5794
[3] vol09 | Анна Каренина | Часть пятая | ru-vol09-анна-каренина-32-4 | 0.5831
[4] vol12 | Отец Сергий | VII | ru-vol12-отец-сергий-115-10 | 0.5802
```

**Refusal demo** (same session, switched to `cite-or-refuse`, labeled as such):

```
chain=cite-or-refuse
[translated from RU sources]
I found nothing on this question in my works.
(no sources)
```

Input was gibberish (`gibberish xyz quantum blah`), refused with no generator
call. (The `[translated from RU sources]` marker is printed by the CLI for
every `answer_lang=en` response, including refusals — cosmetic, real output.)
Exit: clean, no stack trace.

Curator notes: EN answers cite the same RU chunks as the RU session (EN→RU
consistency in action: Q1/Q2 source sets overlap the RU twins). Q3 shows the
honest failure mode — EN generation drifts (Nikodim, Anna Karenina family
talk) while retrieval stays grounded (3/4 Отец Сергий). Translation fidelity,
not retrieval, is the EN weak link — see lessons note 0013.
