# Local runner (0015): fresh clone -> chat with Tolstoy.
# Bare `make` prints help. Wraps the README quickstart commands; every
# wrapped command keeps working standalone. No new dependencies (macOS/Linux).
# NOTE: `CHAT_LANG`/`CHAT_CHAIN` (not LANG/CHAIN) — LANG is set by the shell.

VENV ?= .venv
PY := $(VENV)/bin/python
API_URL := http://127.0.0.1:8000
API_LOG := /tmp/tolstoy-api.log
CHAT_LANG ?= ru
CHAT_CHAIN ?= rerank
EVAL_ARGS ?=

.PHONY: help setup check-corpus index reindex chat eval test

help: ## Show this help (default target).
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## / — /'

setup: ## Create venv, install deps, .env, Ollama model, web deps (idempotent).
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PY) -m pip --version >/dev/null 2>&1 || $(PY) -m ensurepip --upgrade
	$(PY) -m pip install -e ".[dev]"
	test -f .env || cp .env.example .env
	ollama show llama3.2:1b >/dev/null 2>&1 || ollama pull llama3.2:1b
	cd web && npm install
	@echo "setup done — place the 22 EPUBs in data/raw/ (see docs/data-sources.md), then: make chat"

check-corpus: ## Fail fast when data/raw/ lacks the 22 EPUB volumes.
	test -d data/raw || (echo "missing data/raw/ — see docs/data-sources.md" && exit 1)
	test "$$(find data/raw -maxdepth 1 -name '*.epub' | wc -l | tr -d ' ')" -ge 22 || \
		(echo "data/raw/ needs the 22 RU EPUB volumes — see docs/data-sources.md" && exit 1)
	@echo "corpus ok"

index: check-corpus ## Build manifest/clean/.chroma unless already populated.
	test -n "$$(ls -A .chroma 2>/dev/null)" && echo "index already populated — skipping (make reindex to rebuild)" || \
		($(PY) -m tolstoy.manifest build && $(PY) -m tolstoy.clean --all && $(PY) -m tolstoy.index build --all)

reindex: check-corpus ## Force full rebuild (upserts are idempotent on chunk_id).
	$(PY) -m tolstoy.manifest build && $(PY) -m tolstoy.clean --all && $(PY) -m tolstoy.index build --all

chat: index ## Talk to Tolstoy (API lifecycle handled; CHAT_LANG=ru|en CHAT_CHAIN=<name>).
	trap 'kill $$API_PID 2>/dev/null' EXIT INT TERM; \
	$(PY) -m uvicorn tolstoy.api.app:app --host 127.0.0.1 --port 8000 >$(API_LOG) 2>&1 & \
	API_PID=$$!; \
	for i in $$(seq 1 30); do curl -sf $(API_URL)/health >/dev/null && break || sleep 1; done; \
	curl -sf $(API_URL)/health >/dev/null || (echo "API failed to start — see $(API_LOG)" && exit 1); \
	(cd web && npm run chat --silent -- --lang $(CHAT_LANG) --chain $(CHAT_CHAIN))

eval: ## Run the Phase 5 eval harness (EVAL_ARGS="--questions q01,q02" to slice).
	$(PY) -m tolstoy.evaluate $(EVAL_ARGS)

test: ## Full gates: pytest + ruff + Node typecheck.
	$(PY) -m pytest -q
	$(PY) -m ruff check tolstoy tests
	cd web && npm run typecheck --silent
