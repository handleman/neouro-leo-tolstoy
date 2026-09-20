# AGENTS.md

Project-local agent rules for neouro-leo-tolstoy.

## Skills (project-local only)

- `software-architect` lives at `.opencode/skills/software-architect/SKILL.md`. No global skills are used or required.
- Load it for any architecture review, docs review, design doc, ADR, stack decision, or RAG chain design task.

## Design docs (mandatory location)

- ALL design docs, ADRs, and chain proposals go to `docs/design-docs/` — never to `docs/` root.
- Filename: `NNNN-short-slug.md` (next free number, zero-padded, e.g. `0002-rerank-chain.md`).
- Template: `docs/design-docs/_template.md` (Context, Decision/Proposal, Alternatives, Consequences, Open questions).
- Index: update the table in `docs/design-docs/README.md` on every add.
- `docs/` root holds stable product docs only (`vision`, `architecture`, `stack-decision`, `data-sources`, `roadmap`, `glossary`).

## Repo reality

- `data/raw/` = 22 Russian EPUB volumes (gitignored, primary corpus). English Gutenberg texts are secondary.
- No code scaffolded yet — docs first. Keep docs code-free.
