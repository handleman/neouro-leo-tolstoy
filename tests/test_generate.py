"""Ollama client tests (Phase 4 follow-up): payload contract + error mapping, no server."""

import httpx

from tolstoy.generate import ollama
from tolstoy.generate.ollama import GeneratorUnavailable


class _FakeResponse:
    def __init__(self, body: dict) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._body


def _patch_post(monkeypatch, captured: dict, body: dict | None = None):
    def fake_post(url, json, timeout):
        captured.update({"url": url, "json": json, "timeout": timeout})
        return _FakeResponse(body or {"response": "hi"})

    monkeypatch.setattr(httpx, "post", fake_post)


def test_generate_payload_contract(monkeypatch) -> None:
    captured: dict = {}
    _patch_post(monkeypatch, captured)
    assert ollama.generate("sys", "hello") == "hi"
    assert captured["url"] == "http://localhost:11434/api/generate"
    payload = captured["json"]
    assert payload["model"] == "llama3.2:1b"
    assert payload["system"] == "sys"
    assert payload["prompt"] == "hello"
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0.3
    assert payload["options"]["num_predict"] == 1024
    assert payload["options"]["repeat_penalty"] == 1.2
    assert captured["timeout"] == 60.0


def test_generate_http_error_maps_to_unavailable(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "post", fake_post)
    try:
        ollama.generate("sys", "hello")
    except GeneratorUnavailable as exc:
        assert "llama3.2:1b" in str(exc)
    else:
        raise AssertionError("expected GeneratorUnavailable")


def test_is_reachable_false_on_error(monkeypatch) -> None:
    def fake_get(url, timeout):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "get", fake_get)
    assert ollama.is_reachable() is False
