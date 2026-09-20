# 0014: Deploy compatibility without deploying (constraints for a future online service)

- Status: Draft
- Date: 2026-09-20
- Author: software-architect skill

## Context

No deployment happens in v1: vision non-goals exclude production hosting, auth, and scaling, and 0006 rejects Docker for Phase 0. But the maintainer wants a future online service to be possible without redesign. Risk: local-first shortcuts (hardcoded paths/URLs, stateful API, bundled corpus, Ollama-or-nothing generation) could silently close that door. This ADR sets compatibility constraints — rules the build must obey now — with zero deploy work (no containers, no CI deploy, no auth code).

Note on numbering: `0013` stays reserved for the Phase 6 lessons-learned note promised in 0012.

## Decision / Proposal

Constraints (each is a build rule, verified at its phase gate):

1. **Env-only configuration.** Every deployment-varying value (bind host/port, API base URL, CORS origins, Chroma dir/URL, model ids, timeouts, top-k, thresholds) comes from env via `tolstoy/config.py` (0005 convention 1). No `localhost`, no absolute paths, no ports in logic modules. The server binds the configured host (local default; `0.0.0.0`-capable) — one env change, not a code change.
2. **Stateless API.** FastAPI holds no mutable request state: config + client handles only. All corpus state lives in the store backend; any instance can serve any request. Chain `ask()` takes no caller identity (adding auth later must not change its signature — see 5).
3. **Store behind the `Store` interface.** Chroma file-backed path today (`.chroma/`, gitignored); Chroma server-mode or pgvector/Qdrant tomorrow with no chain changes (stack-decision already requires this abstraction — this ADR makes it a gate, not an aspiration).
4. **Generator behind the narrow `generate(system, user, options?)` interface** (0009). Ollama today; any OpenAI-compatible hosted endpoint tomorrow via URL + key env vars. Keys never touch the repo (`.env` gitignored; `.env.example` carries placeholders only).
5. **No auth now, no auth-shaped code — auth arrives at the edge.** When the service comes, authentication lives in a reverse proxy / API gateway in front of the unchanged API, not in chains or endpoints. Rationale: user identity in `ask()` today would be premature abstraction with no consumer.
6. **One API for all surfaces.** The Node CLI, the future web UI, and any service client all speak the same `/health` + `/search` + `/chat` HTTP/JSON contracts. The web UI later is static assets + the same API (CORS origins from env) — never a second protocol.
7. **Container-friendly layout, no containers yet.** Single `pyproject.toml`, no OS-specific assumptions, no build-time network fetches baked into imports (models download at setup/run, Phase 0 smoke pattern). Dockerfiles/CI deploy are explicitly out of scope until after v1.
8. **Cold-start story: index is rebuildable, never shipped.** `data/raw/` and `.chroma/` are gitignored and stay that way; a deployment re-ingests from the owner's local EPUBs or public-domain downloads using the committed manifest schema + `index build --all` (0008). Nothing in the build may assume a pre-baked local index.
9. **Backpressure knobs from day one.** Request timeouts (0009), top-k clamps (0008: 1–20), and prompt char budgets (0009) are config — the same knobs a service uses for latency/SLO control later.

## Alternatives

- **Deploy now (Docker + hosted DB + auth)** — rejected: contradicts the learning-first scope; ops would crowd out RAG fundamentals. This ADR is the compromise: option value without ops cost.
- **User identity plumbed through chains preemptively** — rejected: no consumer, speculative generality; edge-auth (5) covers the future without touching `ask()`.
- **Bundling a prebuilt index as a release artifact** — rejected: corpus is gitignored and license-sensitive; rebuild-from-manifest (8) is the only shippable story.
- **Second (service-only) API surface later** — rejected (6): one contract, three consumers (CLI now; web UI + service later).

## Consequences

- Phase gates gain a compat check: no hardcoded hosts/paths/ports, no stateful endpoints, no new API protocols, no committed secrets or corpus data.
- 0006's no-Docker call stands; this ADR constrains code shape, not packaging.
- Phase 6's future-decisions list (0012 Step 4) gains service deployment alongside web UI / frameworks / EN corpus — decided then, enabled now.
- Stable docs get one-line pointers (vision non-goals, architecture §6, stack alternatives) so the stance is visible without relitigating scope.

## Open questions

1. CORS default posture (locked-down vs permissive-local) — set in Phase 3 CLI work from env; default deny-with-localhost-allowlist.
2. Rate limiting: gateway concern (see 5) or lightweight middleware later? Default gateway; revisit only with abuse evidence.
3. Prebuilt-index distribution if the corpus ever gains a redistributable core — blocked on licensing review, not engineering.
