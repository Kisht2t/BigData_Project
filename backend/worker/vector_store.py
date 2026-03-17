"""Qdrant Cloud client wrapper."""

from __future__ import annotations

import os
from functools import lru_cache

from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from embedder import VECTOR_SIZE

_COLLECTION = os.getenv("QDRANT_COLLECTION", "tech_news")


@lru_cache(maxsize=1)
def _get_client() -> _QdrantClient:
    return _QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )


def ensure_collection() -> None:
    """Create collection and payload index if they don't exist (idempotent)."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if _COLLECTION not in existing:
        client.create_collection(
            collection_name=_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    # Ensure keyword index on source field for filtered search
    client.create_payload_index(
        collection_name=_COLLECTION,
        field_name="source",
        field_schema=PayloadSchemaType.KEYWORD,
    )


def upsert_chunks(chunks: list[dict]) -> int:
    """
    Upsert document chunks into Qdrant.
    Each chunk dict: {id, text, source, title, url, metadata}
    Returns number of points upserted.
    """
    from embedder import embed

    client = _get_client()
    texts = [c["text"] for c in chunks]
    vectors = embed(texts)

    points = [
        PointStruct(
            id=chunk["id"],
            vector=vector,
            payload={
                "text": chunk["text"],
                "source": chunk["source"],
                "title": chunk["title"],
                "url": chunk["url"],
                **chunk.get("metadata", {}),
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    client.upsert(collection_name=_COLLECTION, points=points)
    return len(points)


def search(query_vector: list[float], source: str, top_k: int = 5) -> list[dict]:
    """Search Qdrant filtered by source type. Returns list of chunk dicts."""
    client = _get_client()
    response = client.query_points(
        collection_name=_COLLECTION,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=source))]
        ),
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "text": hit.payload.get("text", ""),
            "source": hit.payload.get("source", source),
            "title": hit.payload.get("title", ""),
            "url": hit.payload.get("url", ""),
            "score": hit.score,
            "metadata": {
                k: v
                for k, v in hit.payload.items()
                if k not in ("text", "source", "title", "url")
            },
        }
        for hit in response.points
    ]
