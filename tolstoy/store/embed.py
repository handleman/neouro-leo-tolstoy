"""Embedder: lazy singleton multilingual model (0008 step 2).

Corpus chunks and queries share the single configured model
(`TOLSTOY_EMBED_MODEL`) — no English model, no second path in v1.
The model loads on first use so `import` stays light (API tests and
CLIs that never embed pay nothing).
"""

from tolstoy.config import load_settings

_model = None
_model_name: str | None = None


def reset_model_cache() -> None:
    """Drop the cached model (tests only)."""
    global _model, _model_name
    _model = None
    _model_name = None


def get_model():  # -> SentenceTransformer (import kept local for light import)
    """Load (once) and return the configured sentence-transformer."""
    global _model, _model_name
    from sentence_transformers import SentenceTransformer

    wanted = load_settings().embed_model
    if _model is None or _model_name != wanted:
        _model = SentenceTransformer(wanted)
        _model_name = wanted
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Batch-encode corpus texts -> vectors (same order as input)."""
    model = get_model()
    vectors = model.encode(texts, batch_size=64, show_progress_bar=False)
    return [list(map(float, row)) for row in vectors]


def embed_query(text: str) -> list[float]:
    """Encode a single query with the same model as the corpus."""
    model = get_model()
    vector = model.encode([text], show_progress_bar=False)[0]
    return list(map(float, vector))
