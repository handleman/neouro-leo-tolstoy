# 0016: Index release — downloadable built store so chat runs without the corpus

- Status: Draft
- Date: 2026-09-27
- Author: software-architect skill

## Context

`data/raw/` (22 EPUBs, 25M), `data/clean/` (35M), and `.chroma/` (386M) are
all gitignored by design, so a fresh clone cannot reach `make chat`: the
corpus gate stops it, and the corpus itself is a personal book collection,
not a redistributable artifact. Goal: a stranger runs the Tolstoy chat with
one download and zero tomes, while owners of *different* tomes keep a
first-class rebuild path. Repo is public (`handleman/neouro-leo-tolstoy`),
so unauthenticated downloads work. Runtime needs beyond the store —
embedder (auto-downloaded from HF) and Ollama model (`ollama pull`) — stay
in `make setup`; the release covers only what cannot be fetched elsewhere.

## Decision / Proposal

Publish the **built `tolstoy-ru` Chroma store as a versioned GitHub Release
asset**; the runner prefers local build, falls back to download.

- **Asset contents:** `.chroma/` contents only (sqlite + segments, 386M at
  v1: 26,188 chunks) as `tolstoy-ru-chroma.tar.gz` (stable name, versioned
  by the release tag) plus a `.sha256` sidecar. NOT published: raw EPUBs (user's own books, distribution weight),
  `data/clean/` (regenerable), `data/manifest.json` (already committed in
  git). Release notes pin the build contract: embed model id, chunk
  900/150/50, chunk count, manifest commit SHA, builder date, `chromadb`
  version from `pyproject.toml` (consumer must `make setup` first so
  versions match — Chroma segment format is version-sensitive).
- **Tagging:** data-only tag `index-tolstoy-ru-v1`, decoupled from the code
  `v1` tag (still the maintainer's call per STATUS). Rationale: the index
  rebuilds on re-chunking or corpus change with zero code diff — it needs
  its own version line (`index-tolstoy-ru-v2`, …). Rebuilds replace the
  asset under a new tag; tags never move.
- **Consumer contract (`make fetch-index`):** `curl -L` the asset URL (no
  auth, no `gh` dependency for readers — `gh` is used only to publish),
  verify SHA256, extract into `.chroma/`, then prove it with `index stats`
  (collection `tolstoy-ru`, expected chunk count from the release notes).
  Any step fails → clear error, no half-extracted store left behind
  (extract to temp dir, verify, swap in).
- **Runner priority in `make index`:** (1) `.chroma/` populated → skip;
  (2) corpus present (`check-corpus`) → local build (source of truth wins);
  (3) otherwise → `fetch-index`. `make chat` therefore works corpus-free.
  `make reindex` always rebuilds locally and requires the corpus — it is
  the documented path for users whose tomes differ from ours.
- **Rebuild path for different tomes:** place any RU EPUBs in `data/raw/`,
  `make reindex`; eval bank expectations are work-name based, so a
  different edition still scores as long as work titles match (noted in
  README + `data-sources.md`). No code changes needed for a new corpus.

## Alternatives

- **Commit `.chroma/` to git** — rejected: 386M of sqlite/segments in
  history, churn on every reindex, clones pay the cost forever.
- **Hugging Face Hub dataset** — rejected: second platform + account for
  zero gain while the code already lives on GitHub Releases.
- **Publish raw EPUBs in the release** — rejected: they are the user's own
  books; redistribution weight and licensing posture stay with the user.
- **`gh release download` for consumers** — rejected: requires `gh` +
  auth where `curl` needs neither on a public repo. `gh` stays a
  maintainer-side publish tool.
- **Single `v1` release bundling code + index** — rejected: couples the
  code milestone to data rebuilds; the maintainer's `v1` code tag stays
  independent.

## Consequences

- Easier: stranger path becomes prerequisites → `make setup` → `make chat`
  (≈400M download replaces the corpus hunt). Harder: none for builders —
  publish is one `gh` command after a rebuild.
- New obligations: checksum discipline, build-contract notes per release,
  new tag per rebuild (stale index after chunk retuning is a real foot-gun
  — the notes + stats check mitigate it).
- Trust model: release asset is opaque vectors; SHA256 covers transit, and
  the local-build path stays available for anyone who wants
  byte-provenance from their own books.

## Open questions

1. Mirror/CDN if the asset outgrows comfortable GitHub asset size (2GB
  hard limit; currently 386M — not a problem yet).
2. Automating publish-on-reindex (CI workflow) — deferred until the second
  rebuild proves the manual path.
3. `v1` code tag timing — unchanged, maintainer's call.
