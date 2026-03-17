"""Tests for the text chunker."""

import os
import sys

# Resolve ingestion/ relative to this file regardless of working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ingestion")))

from chunker import chunk_text


def test_short_text_produces_one_chunk():
    chunks = chunk_text(
        text="Short text.",
        title="Test",
        url="https://example.com",
        source="arxiv",
    )
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short text."
    assert chunks[0]["source"] == "arxiv"
    assert chunks[0]["title"] == "Test"


def test_long_text_produces_multiple_chunks():
    long_text = "word " * 1000  # ~5000 chars, well over one chunk
    chunks = chunk_text(
        text=long_text,
        title="Long Doc",
        url="https://example.com/long",
        source="hackernews",
        chunk_size=100,
        overlap=10,
    )
    assert len(chunks) > 1


def test_chunks_have_stable_ids():
    chunks1 = chunk_text("Hello world", "T", "https://x.com", "github")
    chunks2 = chunk_text("Hello world", "T", "https://x.com", "github")
    assert chunks1[0]["id"] == chunks2[0]["id"]


def test_chunk_ids_are_unique_per_offset():
    long_text = "x " * 600
    chunks = chunk_text(long_text, "T", "https://x.com", "arxiv", chunk_size=100, overlap=10)
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique"
