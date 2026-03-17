"""FastAPI route definitions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from shared.models import AskRequest, AskResponse, IngestRequest
from agents.orchestrator import OrchestratorAgent
from ingestion_client import IngestClient

router = APIRouter()
_orchestrator = OrchestratorAgent()
_ingest_client = IngestClient()


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """Submit a question to the multi-agent research pipeline."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return await _orchestrator.answer(request.question, request.session_id, request.context)


@router.get("/history/{session_id}")
async def get_history(session_id: str) -> list[dict]:
    """Return conversation history for a session (most recent first)."""
    items = _orchestrator.get_history(session_id)
    return [item.model_dump() for item in reversed(items)]


@router.post("/ingest")
async def ingest(request: IngestRequest) -> dict:
    """Ingest a single URL or arXiv paper into the knowledge base."""
    result = await _ingest_client.ingest(request)
    return {"status": "success", "chunks_added": result.chunks_added, "title": result.title}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
