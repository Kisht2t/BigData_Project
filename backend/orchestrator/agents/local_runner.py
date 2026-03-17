"""
Local mode runner — bypasses SQS/DynamoDB entirely.
Used when ENVIRONMENT=local and LocalStack is not running.
Calls worker retrieval logic directly in the same process.
"""

from __future__ import annotations

import sys
import os

# Worker is symlinked at orchestrator root — add it to path
_WORKER_DIR = os.path.join(os.path.dirname(__file__), "..", "worker")
if _WORKER_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(_WORKER_DIR))

from shared.models import AgentTask, RetrievalResult, RetrievedChunk, SourceType
from embedder import embed_one
from vector_store import search, ensure_collection


def run_retrieval(task: AgentTask) -> RetrievalResult:
    """Run retrieval directly without SQS/DynamoDB."""
    ensure_collection()
    query_vector = embed_one(task.sub_question)
    raw_chunks = search(
        query_vector,
        source=task.source_type.value,
        top_k=int(os.getenv("WORKER_MAX_RESULTS_PER_QUERY", "5")),
    )
    return RetrievalResult(
        correlation_id=task.correlation_id,
        source=task.source_type,
        chunks=[RetrievedChunk(**c) for c in raw_chunks],
        sub_question=task.sub_question,
    )
