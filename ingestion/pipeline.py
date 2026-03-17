"""Ingestion pipeline — orchestrates fetch → chunk → embed → upsert."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, "/app/shared")

from chunker import chunk_text
from sources.arxiv_fetcher import ArxivFetcher
from sources.hn_fetcher import HackerNewsFetcher
from sources.github_fetcher import GitHubFetcher

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_ARXIV_MAX = int(os.getenv("ARXIV_MAX_RESULTS", "50"))
_HN_MAX = int(os.getenv("HN_MAX_RESULTS", "100"))
_GITHUB_MAX = int(os.getenv("GITHUB_MAX_REPOS", "30"))

# Topics for pre-populated ingestion
_ARXIV_TOPICS = [
    "large language models",
    "retrieval augmented generation",
    "transformer architecture",
    "diffusion models",
    "graph neural networks",
]

_HN_TOPICS = [
    "machine learning",
    "open source AI",
    "rust programming",
    "kubernetes",
    "vector database",
]

_GITHUB_TOPICS = [
    "llm inference",
    "rag pipeline",
    "embedding model",
    "mlops",
    "vector search",
]


def _get_qdrant():
    sys.path.insert(0, "/app/worker")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend/worker"))
    from vector_store import upsert_chunks, ensure_collection
    ensure_collection()
    return upsert_chunks


async def run_full_ingestion() -> dict:
    """Full pre-populated ingestion run. Called by scheduled ECS task."""
    upsert = _get_qdrant()
    total = 0

    log.info("Starting arXiv ingestion...")
    fetcher = ArxivFetcher()
    for topic in _ARXIV_TOPICS:
        docs = fetcher.fetch(topic, max_results=_ARXIV_MAX // len(_ARXIV_TOPICS))
        for doc in docs:
            chunks = chunk_text(**doc)
            upsert(chunks)
            total += len(chunks)
        log.info(f"arXiv [{topic}]: {len(docs)} papers ingested")

    log.info("Starting Hacker News ingestion...")
    hn_fetcher = HackerNewsFetcher()
    for topic in _HN_TOPICS:
        docs = hn_fetcher.fetch(topic, max_results=_HN_MAX // len(_HN_TOPICS))
        for doc in docs:
            chunks = chunk_text(**doc)
            upsert(chunks)
            total += len(chunks)
        log.info(f"HN [{topic}]: {len(docs)} stories ingested")

    log.info("Starting GitHub ingestion...")
    gh_fetcher = GitHubFetcher()
    for topic in _GITHUB_TOPICS:
        docs = gh_fetcher.fetch(topic, max_results=_GITHUB_MAX // len(_GITHUB_TOPICS))
        for doc in docs:
            chunks = chunk_text(**doc)
            upsert(chunks)
            total += len(chunks)
        log.info(f"GitHub [{topic}]: {len(docs)} repos ingested")

    log.info(f"Full ingestion complete. Total chunks: {total}")
    return {"total_chunks": total}


async def ingest_single(url: str | None = None, arxiv_id: str | None = None) -> dict:
    """On-demand ingestion of a single URL or arXiv paper."""
    upsert = _get_qdrant()

    if arxiv_id:
        fetcher = ArxivFetcher()
        doc = fetcher.fetch_by_id(arxiv_id)
        if not doc:
            return {"chunks_added": 0, "title": "Not found"}
        chunks = chunk_text(**doc)
        upsert(chunks)
        return {"chunks_added": len(chunks), "title": doc["title"]}

    if url:
        from sources.url_fetcher import fetch_url
        doc = fetch_url(url)
        chunks = chunk_text(**doc)
        upsert(chunks)
        return {"chunks_added": len(chunks), "title": doc["title"]}

    return {"chunks_added": 0, "title": ""}


if __name__ == "__main__":
    asyncio.run(run_full_ingestion())
