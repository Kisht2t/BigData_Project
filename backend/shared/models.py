"""Shared Pydantic models used by both orchestrator and worker services."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    GITHUB = "github"


class AgentTask(BaseModel):
    """Message published to SQS by the Orchestrator for each sub-question."""

    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sub_question: str
    source_type: SourceType
    original_question: str


class RetrievalResult(BaseModel):
    """Written to DynamoDB by the Retriever Worker after Qdrant search."""

    correlation_id: str
    source: SourceType
    chunks: list[RetrievedChunk]
    sub_question: str


class RetrievedChunk(BaseModel):
    """A single retrieved document chunk with metadata."""

    text: str
    source: SourceType
    title: str
    url: str
    score: float  # Qdrant similarity score
    metadata: dict = Field(default_factory=dict)


class AskRequest(BaseModel):
    question: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Optional context injected by the frontend (e.g. recently ingested paper title)
    context: Optional[str] = None


class IngestRequest(BaseModel):
    url: Optional[str] = None
    arxiv_id: Optional[str] = None  # e.g. "2310.06825"

    def model_post_init(self, __context: object) -> None:
        if not self.url and not self.arxiv_id:
            raise ValueError("Either url or arxiv_id must be provided")


class SourceAttribution(BaseModel):
    source: SourceType
    title: str
    url: str
    contribution: str  # Brief description of what this source contributed


class Contradiction(BaseModel):
    claim_a: str
    claim_b: str
    source_a: SourceType
    source_b: SourceType


class HistoryItem(BaseModel):
    """One conversation turn stored in DynamoDB history table."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    question: str
    answer: str
    sources: list[SourceAttribution] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    confidence: str = "Medium"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: int = Field(default_factory=lambda: int(time.time()) + 90 * 24 * 60 * 60)


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceAttribution]
    contradictions: list[Contradiction]
    confidence: str  # "High" | "Medium" | "Low"
    session_id: str
