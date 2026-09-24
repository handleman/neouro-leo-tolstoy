"""Config tests: defaults, overrides, .env.example sync."""

import os

from tolstoy.config import KNOWN_ENV_KEYS, load_settings


def _clean_env(monkeypatch) -> None:
    for key in KNOWN_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults_load_with_no_env(monkeypatch) -> None:
    _clean_env(monkeypatch)
    settings = load_settings()
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.api_url == "http://127.0.0.1:8000"
    assert settings.collection == "tolstoy-ru"
    assert settings.embed_model == "paraphrase-multilingual-MiniLM-L12-v2"
    assert settings.ollama_model == "llama3.2:1b"
    assert settings.temperature == 0.3
    assert settings.num_predict == 1024
    assert settings.repeat_penalty == 1.2
    assert settings.generator_timeout == 60.0
    assert settings.chat_context_chars == 6000
    assert settings.top_k == 4
    assert settings.chunk_size == 900
    assert settings.chunk_overlap == 150
    assert settings.default_lang == "ru"


def test_overrides_respected(monkeypatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("TOLSTOY_COLLECTION", "tolstoy-test")
    monkeypatch.setenv("TOLSTOY_TOP_K", "7")
    monkeypatch.setenv("TOLSTOY_TEMPERATURE", "0.9")
    monkeypatch.setenv("TOLSTOY_CORS_ORIGINS", "https://a.example, https://b.example")
    settings = load_settings()
    assert settings.collection == "tolstoy-test"
    assert settings.top_k == 7
    assert settings.temperature == 0.9
    assert settings.cors_origins == ["https://a.example", "https://b.example"]


def test_invalid_numbers_fall_back_to_defaults(monkeypatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("TOLSTOY_TOP_K", "not-a-number")
    assert load_settings().top_k == 4


def test_env_example_keys_known() -> None:
    """Every TOLSTOY_* key in .env.example must exist in KNOWN_ENV_KEYS."""
    example_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.example"
    )
    with open(example_path, encoding="utf-8") as handle:
        documented = {
            line.split("=", 1)[0].strip()
            for line in handle
            if line.strip() and not line.strip().startswith("#")
        }
    documented = {key for key in documented if key.startswith("TOLSTOY_")}
    assert documented == set(KNOWN_ENV_KEYS), (
        f"drift: documented={sorted(documented)} known={sorted(KNOWN_ENV_KEYS)}"
    )
