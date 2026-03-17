"""Tests for the Critic agent — mocks Claude API."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.critic import CriticAgent
from shared.models import RetrievalResult, RetrievedChunk, SourceType


def _make_result(source: SourceType) -> RetrievalResult:
    return RetrievalResult(
        correlation_id="test-id",
        source=source,
        sub_question="test question",
        chunks=[
            RetrievedChunk(
                text="Sample text about the topic.",
                source=source,
                title="Test Paper",
                url="https://example.com",
                score=0.9,
            )
        ],
    )


@pytest.fixture
def mock_claude():
    client = MagicMock()
    response = MagicMock()
    response.content = [
        MagicMock(
            text=json.dumps({
                "answer": "This is the synthesized answer.",
                "sources": [
                    {
                        "source": "arxiv",
                        "title": "Test Paper",
                        "url": "https://example.com",
                        "contribution": "Provided academic context.",
                    }
                ],
                "contradictions": [],
                "confidence": "High",
            })
        )
    ]
    client.messages.create.return_value = response
    return client


def test_critic_returns_ask_response(mock_claude):
    critic = CriticAgent(mock_claude)
    results = [
        _make_result(SourceType.ARXIV),
        _make_result(SourceType.HACKERNEWS),
    ]
    response = critic.synthesize("What is RAG?", "session-1", results)

    assert response.answer == "This is the synthesized answer."
    assert response.confidence == "High"
    assert len(response.sources) == 1
    assert response.session_id == "session-1"


def test_critic_handles_empty_results(mock_claude):
    critic = CriticAgent(mock_claude)
    response = critic.synthesize("What is RAG?", "session-2", [])
    assert response.answer is not None
