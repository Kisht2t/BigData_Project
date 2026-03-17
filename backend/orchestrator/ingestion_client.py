"""Thin client that wraps on-demand ingestion for a single URL/arXiv ID."""

from __future__ import annotations

import sys
import os

from pydantic import BaseModel

# Import ingestion modules — Docker mounts at /ingestion, local dev uses relative path
_INGESTION_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ingestion")
_INGESTION_PATH = "/ingestion" if os.path.isdir("/ingestion") else os.path.abspath(_INGESTION_DIR)
if _INGESTION_PATH not in sys.path:
    sys.path.insert(0, _INGESTION_PATH)

from shared.models import IngestRequest  # noqa: E402


class IngestResult(BaseModel):
    chunks_added: int
    title: str


class IngestClient:
    async def ingest(self, request: IngestRequest) -> IngestResult:
        from pipeline import ingest_single  # lazy import from ingestion service

        result = await ingest_single(url=request.url, arxiv_id=request.arxiv_id)
        return IngestResult(chunks_added=result["chunks_added"], title=result["title"])
