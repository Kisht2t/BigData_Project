"""Tests for prompt templates — verifies placeholders render correctly."""

from agents.prompts import DECOMPOSE_QUESTION_PROMPT, CRITIC_PROMPT


def test_decompose_prompt_renders():
    result = DECOMPOSE_QUESTION_PROMPT.format(question="What is RAG?")
    assert "What is RAG?" in result
    assert "arxiv" in result
    assert "hackernews" in result
    assert "github" in result


def test_critic_prompt_renders():
    result = CRITIC_PROMPT.format(
        question="What is RAG?",
        arxiv_chunks="chunk A",
        hackernews_chunks="chunk B",
        github_chunks="chunk C",
    )
    assert "What is RAG?" in result
    assert "chunk A" in result
    assert "chunk B" in result
    assert "chunk C" in result
    assert "contradictions" in result
    assert "confidence" in result
