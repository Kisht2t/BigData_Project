"""Critic Agent — cross-validates retrieved chunks and synthesizes the final answer."""

from __future__ import annotations

import json
import re

import anthropic


def _strip_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

from shared.models import (
    AskResponse,
    Contradiction,
    HistoryItem,
    RetrievalResult,
    SourceAttribution,
    SourceType,
)
from .prompts import CRITIC_PROMPT

_CLAUDE_MODEL = "claude-sonnet-4-6"
_MAX_CHUNKS_PER_SOURCE = 5
# Anthropic requires >= 1024 tokens for caching to activate (~4000 chars)
_MIN_CACHE_CHARS = 4000


class CriticAgent:
    def __init__(self, claude_client: anthropic.Anthropic) -> None:
        self._claude = claude_client

    def synthesize(
        self,
        question: str,
        session_id: str,
        results: list[RetrievalResult],
        history: list[dict] | None = None,
    ) -> AskResponse:
        chunks_by_source = self._group_by_source(results)

        current_prompt = CRITIC_PROMPT.format(
            question=question,
            arxiv_chunks=self._format_chunks(chunks_by_source.get(SourceType.ARXIV, [])),
            hackernews_chunks=self._format_chunks(
                chunks_by_source.get(SourceType.HACKERNEWS, [])
            ),
            github_chunks=self._format_chunks(chunks_by_source.get(SourceType.GITHUB, [])),
        )

        messages = self._build_messages(current_prompt, history)

        message = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=4096,
            messages=messages,
        )

        data = json.loads(_strip_json(message.content[0].text))

        return AskResponse(
            answer=data["answer"],
            sources=[SourceAttribution(**s) for s in data.get("sources", [])],
            contradictions=[Contradiction(**c) for c in data.get("contradictions", [])],
            confidence=data.get("confidence", "Medium"),
            session_id=session_id,
        )

    def _build_messages(self, current_prompt: str, history: list[dict] | None) -> list[dict]:
        """Build the messages array, using prompt caching on history when large enough."""
        if not history:
            return [{"role": "user", "content": current_prompt}]

        history_text = self._format_history(history)

        # Only apply cache_control if history is large enough for Anthropic to cache it
        if len(history_text) >= _MIN_CACHE_CHARS:
            return [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": history_text,
                            "cache_control": {"type": "ephemeral"},
                        },
                        {
                            "type": "text",
                            "text": current_prompt,
                        },
                    ],
                }
            ]

        # History exists but too small to cache — just prepend as plain text
        return [
            {
                "role": "user",
                "content": history_text + "\n\n" + current_prompt,
            }
        ]

    def _format_history(self, history: list[dict]) -> str:
        lines = ["## Prior conversation in this session (for context only — focus on the new question below):"]
        for i, turn in enumerate(history, 1):
            lines.append(f"\n[Turn {i}]")
            lines.append(f"Q: {turn['question']}")
            lines.append(f"A: {turn['answer'][:500]}{'...' if len(turn['answer']) > 500 else ''}")
        return "\n".join(lines)

    def _group_by_source(self, results: list[RetrievalResult]) -> dict[SourceType, list]:
        grouped: dict[SourceType, list] = {}
        for result in results:
            grouped.setdefault(result.source, [])
            grouped[result.source].extend(result.chunks[:_MAX_CHUNKS_PER_SOURCE])
        return grouped

    def _format_chunks(self, chunks: list) -> str:
        if not chunks:
            return "(no results retrieved)"
        parts = []
        for i, chunk in enumerate(chunks[:_MAX_CHUNKS_PER_SOURCE], 1):
            text = chunk.text[:600] if len(chunk.text) > 600 else chunk.text
            parts.append(f"[{i}] {chunk.title}\nURL: {chunk.url}\n{text}")
        return "\n\n".join(parts)
