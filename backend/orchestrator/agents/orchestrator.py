"""Orchestrator Agent — decomposes user questions and dispatches to SQS (or runs locally)."""

from __future__ import annotations

import json
import os
import time
import uuid
import re

import anthropic

from shared.models import (
    AgentTask, AskResponse, HistoryItem, RetrievalResult, SourceType,
)
from .critic import CriticAgent
from .prompts import DECOMPOSE_QUESTION_PROMPT

_CLAUDE_MODEL = "claude-sonnet-4-6"
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
_RESULT_TIMEOUT = int(os.getenv("WORKER_RESULT_TIMEOUT_SECONDS", "30"))
_HISTORY_WINDOW = 10  # number of past Q&A pairs to include as context

# In-memory history store for local mode (per-process, not persistent across restarts)
_LOCAL_HISTORY: dict[str, list[dict]] = {}


def _strip_json(text: str) -> str:
    """Strip markdown code fences Claude sometimes wraps JSON in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class OrchestratorAgent:
    def __init__(self) -> None:
        self._claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._critic = CriticAgent(self._claude)
        self._local = _ENVIRONMENT == "local"

        if not self._local:
            from boto3.dynamodb.conditions import Key
            from shared.aws_clients import get_dynamodb_resource, get_sqs_client
            self._sqs = get_sqs_client()
            dynamo = get_dynamodb_resource()
            self._table = dynamo.Table(os.environ["DYNAMODB_TABLE_NAME"])
            self._history_table = dynamo.Table(os.environ["DYNAMODB_HISTORY_TABLE"])
            self._Key = Key

    async def answer(self, question: str, session_id: str, context: str | None = None) -> AskResponse:
        # Fetch prior conversation history for this session
        history = self._get_history(session_id)

        # Augment question with recently ingested context if provided
        effective_question = (
            f"[Context: the user just added this source — {context}]\n\n{question}"
            if context
            else question
        )

        # Decompose — pass last 3 history items so Claude handles follow-ups like "expand on that"
        sub_questions = self._decompose(effective_question, history[-3:])

        if self._local:
            results = self._run_local(sub_questions, session_id)
        else:
            correlation_id = str(uuid.uuid4())
            self._dispatch_to_sqs(sub_questions, correlation_id, session_id, question)
            results = self._collect_results(correlation_id, expected=len(sub_questions))

        response = self._critic.synthesize(effective_question, session_id, results, history)

        # Persist this turn to history
        self._save_history(session_id, question, response)

        return response

    def get_history(self, session_id: str) -> list[HistoryItem]:
        """Public method for the /history route."""
        raw = self._get_history(session_id)
        return [HistoryItem(**item) for item in raw]

    def _get_history(self, session_id: str) -> list[dict]:
        """Fetch last _HISTORY_WINDOW turns from storage."""
        if self._local:
            return list(_LOCAL_HISTORY.get(session_id, []))[-_HISTORY_WINDOW:]

        from boto3.dynamodb.conditions import Key
        response = self._history_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=True,  # oldest first
            Limit=_HISTORY_WINDOW,
        )
        items = response.get("Items", [])
        # Re-query for most recent window if there are more
        if response.get("LastEvaluatedKey"):
            response = self._history_table.query(
                KeyConditionExpression=Key("session_id").eq(session_id),
                ScanIndexForward=False,
                Limit=_HISTORY_WINDOW,
            )
            items = list(reversed(response.get("Items", [])))
        return items

    def _save_history(self, session_id: str, question: str, response: AskResponse) -> None:
        """Persist one conversation turn."""
        item = HistoryItem(
            session_id=session_id,
            question=question,
            answer=response.answer,
            sources=response.sources,
            contradictions=response.contradictions,
            confidence=response.confidence,
        )
        if self._local:
            _LOCAL_HISTORY.setdefault(session_id, []).append(item.model_dump())
        else:
            self._history_table.put_item(Item=item.model_dump())

    def _decompose(self, question: str, recent_history: list[dict]) -> dict[str, str]:
        history_prefix = ""
        if recent_history:
            lines = []
            for turn in recent_history[-3:]:
                lines.append(f"Q: {turn['question']}\nA: {turn['answer'][:300]}...")
            history_prefix = "Recent conversation:\n" + "\n\n".join(lines) + "\n\n"

        prompt = history_prefix + DECOMPOSE_QUESTION_PROMPT.format(question=question)
        message = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_strip_json(message.content[0].text))

    def _run_local(self, sub_questions: dict[str, str], session_id: str) -> list[RetrievalResult]:
        from .local_runner import run_retrieval
        results = []
        for source_type, sub_question in sub_questions.items():
            task = AgentTask(
                correlation_id=str(uuid.uuid4()),
                session_id=session_id,
                sub_question=sub_question,
                source_type=SourceType(source_type),
                original_question="",
            )
            results.append(run_retrieval(task))
        return results

    def _dispatch_to_sqs(
        self,
        sub_questions: dict[str, str],
        correlation_id: str,
        session_id: str,
        question: str,
    ) -> None:
        for source_type, sub_question in sub_questions.items():
            task = AgentTask(
                correlation_id=correlation_id,
                session_id=session_id,
                sub_question=sub_question,
                source_type=SourceType(source_type),
                original_question=question,
            )
            self._sqs.send_message(
                QueueUrl=os.environ["SQS_QUEUE_URL"],
                MessageBody=task.model_dump_json(),
            )

    def _collect_results(self, correlation_id: str, expected: int) -> list[RetrievalResult]:
        deadline = time.time() + _RESULT_TIMEOUT
        while time.time() < deadline:
            response = self._table.query(
                KeyConditionExpression=self._Key("correlation_id").eq(correlation_id)
            )
            items = response.get("Items", [])
            if len(items) >= expected:
                return [RetrievalResult.model_validate(item) for item in items]
            time.sleep(1)
        items = self._table.query(
            KeyConditionExpression=self._Key("correlation_id").eq(correlation_id)
        ).get("Items", [])
        return [RetrievalResult.model_validate(item) for item in items]
