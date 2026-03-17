"""sentence-transformers embedding wrapper — runs in-container, zero cost."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(_MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns list of float vectors."""
    model = _load_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]


VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension
