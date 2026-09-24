"""Ollama generator client (0009 step 1).

Single `generate(system, user) -> text` call against TOLSTOY_OLLAMA_URL /
TOLSTOY_OLLAMA_MODEL. Ollama-down/timeout maps to typed
`GeneratorUnavailable` (API turns it into 503, never a fake answer).
No multi-model retries in v1; model swap is one env var.
"""

import httpx

from tolstoy.config import load_settings


class GeneratorUnavailable(RuntimeError):
    """Raised when Ollama cannot be reached or times out."""


def generate(system: str, user: str, temperature: float | None = None) -> str:
    settings = load_settings()
    payload = {
        "model": settings.ollama_model,
        "system": system,
        "prompt": user,
        "stream": False,
        "options": {
            "temperature": settings.temperature if temperature is None else temperature,
            "num_predict": settings.num_predict,
            "repeat_penalty": settings.repeat_penalty,
        },
    }
    try:
        response = httpx.post(
            f"{settings.ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=settings.generator_timeout,
        )
        response.raise_for_status()
        return str(response.json().get("response", ""))
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise GeneratorUnavailable(f"ollama {settings.ollama_model} unavailable: {exc}") from exc


def is_reachable() -> bool:
    """Best-effort liveness probe for /health (never raises)."""
    settings = load_settings()
    try:
        response = httpx.get(
            f"{settings.ollama_url.rstrip('/')}/api/tags",
            timeout=min(settings.generator_timeout, 5.0),
        )
        return response.status_code == 200
    except httpx.HTTPError:
        return False
