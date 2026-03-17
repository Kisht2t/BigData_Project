"""Retriever Worker — long-polls SQS, retrieves from Qdrant, writes results to DynamoDB."""

from __future__ import annotations

import json
import logging
import os
import time

from shared.aws_clients import get_dynamodb_resource, get_sqs_client
from shared.models import AgentTask, RetrievalResult, RetrievedChunk, SourceType
from embedder import embed_one
from vector_store import search, ensure_collection
from retrievers.arxiv import ArxivRetriever
from retrievers.hackernews import HackerNewsRetriever
from retrievers.github import GitHubRetriever

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
_DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE_NAME"]
_POLL_WAIT = int(os.getenv("WORKER_POLL_WAIT_SECONDS", "20"))
_TOP_K = int(os.getenv("WORKER_MAX_RESULTS_PER_QUERY", "5"))

_RETRIEVERS = {
    SourceType.ARXIV: ArxivRetriever(),
    SourceType.HACKERNEWS: HackerNewsRetriever(),
    SourceType.GITHUB: GitHubRetriever(),
}


def process_task(task: AgentTask) -> None:
    """Embed sub-question, search Qdrant, write results to DynamoDB."""
    log.info(f"Processing task: {task.source_type} — {task.sub_question[:60]}")

    query_vector = embed_one(task.sub_question)
    raw_chunks = search(query_vector, source=task.source_type.value, top_k=_TOP_K)

    chunks = [RetrievedChunk(**c) for c in raw_chunks]
    result = RetrievalResult(
        correlation_id=task.correlation_id,
        source=task.source_type,
        chunks=chunks,
        sub_question=task.sub_question,
    )

    # Write to DynamoDB
    dynamo = get_dynamodb_resource()
    table = dynamo.Table(_DYNAMODB_TABLE)
    table.put_item(Item=result.model_dump())
    log.info(f"Wrote {len(chunks)} chunks to DynamoDB for correlation_id={task.correlation_id}")


def run() -> None:
    ensure_collection()
    sqs = get_sqs_client()
    log.info("Retriever worker started, polling SQS...")

    while True:
        response = sqs.receive_message(
            QueueUrl=_SQS_QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=_POLL_WAIT,
        )
        messages = response.get("Messages", [])

        for message in messages:
            try:
                task = AgentTask.model_validate_json(message["Body"])
                process_task(task)
                sqs.delete_message(
                    QueueUrl=_SQS_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"],
                )
            except Exception as exc:
                log.error(f"Failed to process message: {exc}", exc_info=True)
                # Message will re-appear in queue after visibility timeout


if __name__ == "__main__":
    run()
