"""Text chunking with sliding window (token-aware via character approximation)."""

from __future__ import annotations

import hashlib
import os
import uuid

_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))  # tokens ≈ chars / 4
_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# Approximate chars per token for English text
_CHARS_PER_TOKEN = 4


def chunk_text(
    text: str,
    title: str,
    url: str,
    source: str,
    metadata: dict | None = None,
    chunk_size: int = _CHUNK_SIZE,
    overlap: int = _CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split text into overlapping chunks.
    Returns list of chunk dicts ready for Qdrant upsert.
    """
    char_size = chunk_size * _CHARS_PER_TOKEN
    char_overlap = overlap * _CHARS_PER_TOKEN

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_size
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id = _stable_id(url, start)
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "title": title,
                "url": url,
                "source": source,
                "metadata": {
                    "chunk_start": start,
                    **(metadata or {}),
                },
            })

        start += char_size - char_overlap

    return chunks


def _stable_id(url: str, offset: int) -> str:
    """Generate a stable deterministic UUID for a chunk (Qdrant requires UUID or int)."""
    key = f"{url}::{offset}"
    digest = hashlib.sha256(key.encode()).digest()
    return str(uuid.UUID(bytes=digest[:16]))
