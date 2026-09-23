"""Single env-driven settings source (0005 convention 1).

Every tunable lives here with its documented default. No hardcoded
constants in logic modules. All deployment-varying values come from
the environment so a future online service needs no code changes (0014).
"""

import os
from dataclasses import dataclass, field


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _get_list(key: str, default: list[str]) -> list[str]:
    raw = os.environ.get(key)
    if raw is None or not raw.strip():
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    # API surface
    api_host: str = field(default_factory=lambda: _get("TOLSTOY_API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: _get_int("TOLSTOY_API_PORT", 8000))
    api_url: str = field(default_factory=lambda: _get("TOLSTOY_API_URL", "http://127.0.0.1:8000"))
    cors_origins: list[str] = field(
        default_factory=lambda: _get_list("TOLSTOY_CORS_ORIGINS", ["http://localhost:3000"])
    )
    # Vector memory (sole v1 collection: tolstoy-ru)
    chroma_dir: str = field(default_factory=lambda: _get("TOLSTOY_CHROMA_DIR", ".chroma"))
    collection: str = field(default_factory=lambda: _get("TOLSTOY_COLLECTION", "tolstoy-ru"))
    embed_model: str = field(
        default_factory=lambda: _get("TOLSTOY_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    )
    # Generator (Ollama today; any OpenAI-compatible endpoint tomorrow via URL+key env)
    ollama_url: str = field(
        default_factory=lambda: _get("TOLSTOY_OLLAMA_URL", "http://localhost:11434")
    )
    ollama_model: str = field(default_factory=lambda: _get("TOLSTOY_OLLAMA_MODEL", "llama3.2:1b"))
    temperature: float = field(default_factory=lambda: _get_float("TOLSTOY_TEMPERATURE", 0.3))
    # Retrieval / chunking
    top_k: int = field(default_factory=lambda: _get_int("TOLSTOY_TOP_K", 4))
    chunk_size: int = field(default_factory=lambda: _get_int("TOLSTOY_CHUNK_SIZE", 900))
    chunk_overlap: int = field(default_factory=lambda: _get_int("TOLSTOY_CHUNK_OVERLAP", 150))
    chunk_min_chars: int = field(default_factory=lambda: _get_int("TOLSTOY_CHUNK_MIN_CHARS", 50))
    score_threshold: float = field(
        default_factory=lambda: _get_float("TOLSTOY_SCORE_THRESHOLD", 0.0)
    )
    rerank_broad_k: int = field(default_factory=lambda: _get_int("TOLSTOY_RERANK_BROAD_K", 12))
    # Chat language default (ru; en = translation of RU-grounded answer)
    default_lang: str = field(default_factory=lambda: _get("TOLSTOY_DEFAULT_LANG", "ru"))


def load_settings() -> Settings:
    """Read settings from the environment (fresh on every call; cheap)."""
    return Settings()


#: All TOLSTOY_* keys documented in .env.example. Tests assert these stay in sync.
KNOWN_ENV_KEYS = (
    "TOLSTOY_API_HOST",
    "TOLSTOY_API_PORT",
    "TOLSTOY_API_URL",
    "TOLSTOY_CORS_ORIGINS",
    "TOLSTOY_CHROMA_DIR",
    "TOLSTOY_COLLECTION",
    "TOLSTOY_EMBED_MODEL",
    "TOLSTOY_OLLAMA_URL",
    "TOLSTOY_OLLAMA_MODEL",
    "TOLSTOY_TEMPERATURE",
    "TOLSTOY_TOP_K",
    "TOLSTOY_CHUNK_SIZE",
    "TOLSTOY_CHUNK_OVERLAP",
    "TOLSTOY_CHUNK_MIN_CHARS",
    "TOLSTOY_SCORE_THRESHOLD",
    "TOLSTOY_RERANK_BROAD_K",
    "TOLSTOY_DEFAULT_LANG",
)
