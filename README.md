# MARS — Multi-Agent Research Synthesizer

A portfolio-grade Big Data system where users ask complex tech and science questions and receive cross-validated answers synthesized from three specialized AI agents searching academic papers, tech community discussions, and open-source projects simultaneously.

> Built entirely without orchestration frameworks (no LangChain, no LlamaIndex). Every Claude API call is written directly, every prompt is visible, every design decision is intentional.

---

## What It Does

You type: *"How does vLLM compare to llama.cpp for running LLMs in production?"*

The system:
1. **Decomposes** the question into 3 targeted sub-questions via Claude
2. **Dispatches** each sub-question to a specialized retrieval agent via AWS SQS
3. **Retrieves** semantically relevant content from Qdrant (arXiv papers, HN discussions, GitHub READMEs)
4. **Cross-validates** all retrieved chunks, detects contradictions, assigns confidence scores via Claude
5. **Returns** a structured answer with inline citations, source cards, and contradiction alerts

Total latency: 8-15 seconds end-to-end.

---

## Architecture

```
User Question
     │
     ▼
API Gateway (HTTP API)
     │
     ▼
ECS Fargate — Orchestrator (FastAPI)
     │  Claude decomposes question → 3 sub-questions
     │  Publishes 3 messages to SQS (tagged: arxiv | hackernews | github)
     │
     ▼
ECS Fargate — Retriever Worker (polls SQS)
     ├── arXiv retriever
     ├── Hacker News retriever
     └── GitHub README retriever
              │
              ├── sentence-transformers (embed sub-question, in-container)
              ├── Qdrant Cloud (vector similarity search, filtered by source)
              └── DynamoDB (write results keyed by correlation_id)
     │
     ▼
Orchestrator collects results (polls DynamoDB by correlation_id)
     │
     ▼
Claude Critic Agent
     │  Cross-validates chunks across sources
     │  Detects contradictions (claim A vs claim B)
     │  Assigns confidence: High / Medium / Low
     │  Generates answer with inline citations
     │
     ▼
Next.js 14 Frontend
     ├── Agent Pipeline Visualizer (idle → searching → done/failed per source)
     ├── Answer Panel (markdown + confidence badge)
     ├── Source Cards (grouped by arXiv / HN / GitHub)
     ├── Contradiction Alert (expandable amber banner)
     └── Chat History Sidebar (persisted across sessions via DynamoDB)
```

---

## Agent Design — The Key Differentiator

Most RAG demos: embed → search → answer. One round trip. One source.

MARS uses async multi-agent orchestration:

### Orchestrator Agent (Claude claude-sonnet-4-6)

Receives the user's question and decomposes it into 3 source-specific sub-questions:

```
Input:  "What are the best open-source LLM inference frameworks?"

Output: {
  "arxiv":      "What academic research exists on efficient LLM inference optimization techniques?",
  "hackernews": "What do ML engineers say about production LLM serving frameworks?",
  "github":     "What are the most starred open-source LLM inference libraries and their features?"
}
```

Each sub-question is semantically tuned to the retrieval source it targets. An arXiv sub-question uses academic vocabulary. A GitHub sub-question focuses on implementation details. This specificity is what makes the vector search effective.

### Retriever Worker

Long-polls SQS, routes to the correct retriever, embeds the sub-question with `all-MiniLM-L6-v2`, and queries Qdrant with a source filter. The filter is critical — without it, an arXiv sub-question would surface GitHub results and vice versa. Results are written to DynamoDB keyed by `correlation_id`.

### Critic Agent (Claude claude-sonnet-4-6)

Receives all retrieved chunks from all three sources and performs:

1. **Cross-validation**: compares claims across sources for agreement or conflict
2. **Contradiction detection**: if arXiv says "X requires 80GB VRAM" and HN says "X runs on a laptop", that is flagged
3. **Confidence scoring**: High (sources agree, strong evidence), Medium (partial), Low (conflicting or sparse)
4. **Citation mapping**: every claim in the answer is linked to the source document that supports it

The Critic prompt returns structured JSON — not prose — so the frontend can render source cards, contradiction alerts, and confidence badges without parsing free text.

### Conversation Memory (Rolling Window + Prompt Caching)

Each session's history is stored in DynamoDB with a 90-day TTL. On every subsequent question, the last 10 turns are fetched and passed to the Critic as conversation context. When history exceeds ~4,000 characters, an Anthropic `cache_control` block is applied — cached tokens cost 10% of normal input pricing, making long conversations nearly cost-neutral.

Session identity is a UUID stored in `localStorage` — no login required, works across tab closes and browser restarts on the same device.

---

## Data Ingestion Pipeline

Two modes:

### Pre-populated (Scheduled ECS Task)
Runs daily. Fetches and embeds:
- **50 arXiv papers** across 5 ML/AI topics (LLMs, RAG, transformers, diffusion models, graph neural networks)
- **100 Hacker News stories** across 5 tech topics (ML, open-source AI, Rust, Kubernetes, vector databases)
- **30 GitHub READMEs** across 5 engineering topics (LLM inference, RAG pipelines, embedding models, MLOps, vector search)

Total: ~210+ chunks in Qdrant at launch.

Text is chunked at 512 tokens (≈2,048 chars) with 50-token overlap. Chunk IDs are deterministic SHA-256 UUIDs so re-ingesting the same document upserts rather than duplicates.

### On-Demand (User-triggered via `/ingest`)
Users paste any URL or arXiv ID. The system fetches, chunks, embeds, and upserts to Qdrant in real-time. The ingested title is shown as context in the frontend so the next question is automatically scoped to that source.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.12 | Type hints, async native, ecosystem |
| API Framework | FastAPI + uvicorn | Async handlers, automatic OpenAPI docs, Pydantic integration |
| Agent LLM | Claude claude-sonnet-4-6 | Best instruction-following for structured JSON output; prompt caching; 200K context window |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Free, in-container, 384-dim, good semantic quality for English tech text |
| Vector DB | Qdrant Cloud (free tier) | Payload filtering (critical for source separation), fast ANN, no infrastructure to manage |
| Message Queue | AWS SQS | Decouples orchestrator from workers; messages retry automatically on failure; scales to N workers |
| Database | AWS DynamoDB | Serverless, free tier covers portfolio scale, TTL auto-expiry built-in, no schema migrations |
| Object Storage | AWS S3 | Raw document cache for ingestion idempotency |
| Frontend | Next.js 14 (App Router) | React Server Components, standalone Docker build, TypeScript-first |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, no runtime overhead, consistent design tokens |
| Containers | Docker | Reproducible builds, embedding model baked into worker image at build time |
| Orchestration | AWS ECS Fargate | Serverless containers, no EC2 nodes to patch, pay-per-task |
| Load Balancer | AWS ALB | Path-based routing (/ → frontend, /api/* → orchestrator) |
| Registry | AWS ECR | Private container registry colocated with ECS, IAM-gated |
| IaC | Terraform | Reproducible, version-controlled infrastructure; one `apply` recreates everything |
| CI/CD | GitHub Actions | Integrated with repo, 2,000 free minutes/month, matrix builds |
| Secrets | AWS Secrets Manager | Injected as env vars into ECS tasks at runtime; never in code or images |
| Monitoring | AWS CloudWatch | Structured logs from all ECS tasks, 7-day retention |

---

## AWS Infrastructure

All resources are prefixed `mars-` and provisioned via Terraform in `us-east-1`.

### Why ECS Fargate over EKS

EKS (Kubernetes) adds a control plane cost of ~$72/month before running a single container. For a portfolio project with 3 services, that alone would push the budget past the target. ECS Fargate has no control plane cost — you pay only for the vCPU and memory your tasks consume.

ECS also has a lower operational surface. No node groups, no kubeconfig management, no Helm charts. A task definition is a JSON document. A service is a desired count. For 3 microservices with predictable traffic, this is the correct choice.

### Why SQS over direct HTTP between services

If the orchestrator called the worker directly over HTTP, any worker crash would propagate as a failed request to the user. With SQS, the message persists in the queue until a worker successfully processes it and explicitly deletes it. A worker can crash mid-processing and the message will reappear after the visibility timeout.

It also makes the system trivially scalable — run 5 worker tasks and throughput multiplies by 5 with no code changes.

### Why DynamoDB over RDS

The retrieval results pattern is: write once (worker writes), read once (orchestrator collects), then never touch again. RDS is built for relational joins and complex queries across large datasets. DynamoDB is built for key-value access at any scale. Paying for an RDS instance to do simple put/get operations would be wasteful and operationally heavier (VPC subnet configuration, maintenance windows, storage provisioning).

### Why Qdrant over Pinecone

Pinecone's free tier (Starter) is a shared pod with no SLA and limited to 100K vectors. Qdrant Cloud's free tier is 1GB of dedicated storage with a persistent cluster. For a demo with 210 chunks (~5MB of vectors at 384 dimensions × 4 bytes), Qdrant's free tier is more than sufficient.

Qdrant also supports payload filtering natively — the `source` field filter is what lets the system route an arXiv sub-question only to arXiv chunks. Pinecone supports metadata filtering but requires a higher-tier plan for filtered search performance.

### Why sentence-transformers in-container over an embedding API

OpenAI's `text-embedding-3-small` costs $0.02 per million tokens. At ingestion time, embedding 210 chunks is negligible. But at query time, every user question requires 3 embedding calls (one per sub-question) and the response latency adds 200-400ms per call. Baking `all-MiniLM-L6-v2` into the Docker image means embeddings run locally in ~50ms with no API cost and no external dependency. The model is downloaded once at image build time and cached in the layer.

### Cost Breakdown (Monthly)

| Resource | Spec | Est. Cost |
|---|---|---|
| ECS Fargate — Orchestrator | 0.5 vCPU, 1GB, 24/7 | $17.77 |
| ECS Fargate — Worker | 0.25 vCPU, 0.5GB, 24/7 | $8.89 |
| ECS Fargate — Frontend | 0.25 vCPU, 0.5GB, 24/7 | $8.89 |
| ECS Fargate — Ingestion | 0.5 vCPU, 1GB, ~5min/day | $0.50 |
| DynamoDB (results + history) | On-demand, free tier | $0 |
| SQS | Free tier (1M requests/month) | $0 |
| S3 | < 1GB storage | $0.50 |
| ALB | 1 load balancer | $1.50 |
| ECR | 4 repos, < 5GB | $0.50 |
| CloudWatch | Logs + metrics | $1.00 |
| Secrets Manager | 4 secrets | $0.40 |
| API Gateway + data transfer | — | $1.00 |
| Claude API (usage) | ~300 calls/month | $2–5 |
| Qdrant Cloud | Free tier | $0 |
| **Total** | | **$42–47/month** |

Cost optimization: ECS scheduled scaling (0 tasks 10pm–8am) reduces to ~$15–20/month.

---

## Local Development

### Prerequisites
- Python 3.12
- Node.js 20
- Docker (optional, for full stack)

### Setup

```bash
git clone https://github.com/Kisht2t/BigData_Project.git
cd BigData_Project
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, QDRANT_URL, QDRANT_API_KEY
```

### Run backend

```bash
# Terminal 1 — Orchestrator
cd backend/orchestrator
export PYTHONPATH="../../backend/shared:../../backend/worker"
export ENVIRONMENT=local
uvicorn main:app --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev  # http://localhost:3001
```

### Populate Qdrant with seed data

```bash
cd ingestion
export PYTHONPATH="../backend/shared:../backend/worker"
python pipeline.py
# Ingests 50 arXiv papers + 100 HN stories + 30 GitHub repos
```

### Run tests

```bash
cd backend/orchestrator && pytest tests/ -v
cd backend/worker && pytest tests/ -v
```

---

## Deployment

### One-time infrastructure setup

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials

terraform init
terraform plan
terraform apply   # ~4 minutes
```

### GitHub Actions CI/CD

Every push to `main`:
1. CI runs: 12 unit tests + ruff lint + TypeScript type check
2. If CI passes: builds 4 Docker images, pushes to ECR, rolling deploy to ECS

Required GitHub Secrets: `AWS_ACCOUNT_ID`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `AWS_REGION` | `us-east-1` |
| `DYNAMODB_TABLE_NAME` | `mars-results` |
| `DYNAMODB_HISTORY_TABLE` | `mars-history` |
| `SQS_QUEUE_URL` | SQS queue URL |
| `S3_BUCKET_NAME` | S3 bucket for raw docs |
| `ENVIRONMENT` | `local` or `production` |

---

## Key Design Decisions

**No orchestration framework.** LangChain and LlamaIndex abstract away prompts, chains, and retrievers. That abstraction is useful for prototyping but opaque for production debugging. When a Claude response is malformed, you need to see the exact prompt that caused it. Every Claude call in MARS is a direct API call with a visible, editable prompt in `agents/prompts.py`.

**Async via SQS, not threads.** The retrieval step for 3 sources could be parallelized with `asyncio.gather`. It was, in an earlier version. SQS was chosen instead because it survives worker crashes, supports independent scaling, and makes the system observable — every message in the queue is a unit of work you can inspect, replay, and monitor.

**Privacy-first sessions.** No login, no email, no account. A UUID is generated in the browser and persisted in `localStorage`. The recruiter reviewing this project never has to hand over personal information to use the system. The UUID is practically unguessable (2^122 combinations) and tied to that browser on that device.

**Prompt caching as a cost control.** Conversation history grows with each turn. Without caching, sending 10 prior messages with every new question adds ~5,000 tokens at full price on every call. With `cache_control: ephemeral`, those tokens cost 10% after the first request in a session. For active conversations, this makes the rolling-window memory feature nearly cost-neutral.

**Embedding model baked into Docker image.** `all-MiniLM-L6-v2` is downloaded at image build time via a `RUN python -c "SentenceTransformer(...)"` layer. Cold starts don't download the model. The image is larger (~1.5GB) but the worker is always ready to embed immediately.

---

---

## For Recruiters and Interviewers

---

### 90-Second Resume Bullet

**Built and deployed a cloud-native multi-agent AI research system (MARS) on AWS ECS Fargate, processing user questions through a 3-agent async pipeline — Claude-powered decomposition, parallel semantic retrieval across arXiv, Hacker News, and GitHub via Qdrant vector search, and a Claude Critic agent for cross-source contradiction detection and confidence scoring. Implemented conversation memory with DynamoDB persistence and Anthropic prompt caching reducing per-turn context cost by 90%. Delivered full CI/CD via GitHub Actions (12 unit tests, lint gate, Docker build, ECR push, rolling ECS deploy), infrastructure-as-code via Terraform, and a Next.js 14 research UI. Operates at ~$44/month on AWS.**

---

### 3-Minute Interview Talking Points

**1. Why multi-agent instead of a single RAG call?**

The problem with a single RAG call is source homogeneity. If you embed the question and search everything, you get the top-5 most similar chunks — which are often all from the same source type and carry the same perspective. A researcher asking about LLM inference doesn't just want the most popular GitHub repo. They want to know what the academic literature says, what practitioners in the community have discovered in production, and what the actual codebases do differently.

The three-agent design forces source diversity. Each agent receives a sub-question semantically tuned to its source — academic vocabulary for arXiv, practitioner language for HN, implementation focus for GitHub. The Critic then cross-validates across those three perspectives, which is where the real value is. When arXiv says a technique requires 80GB VRAM and an HN thread says someone runs it on a laptop, that contradiction is surfaced to the user explicitly. A single RAG call would just pick whichever chunk scored higher.

**2. How did you handle the cost of sending conversation history to Claude on every turn?**

The naive approach — concatenate all prior messages and send them as plain text — works but gets expensive fast. Ten prior turns is roughly 5,000 extra input tokens on every call. At claude-sonnet-4-6 pricing, that is $0.015 extra per request. Across 300 calls a month, that adds $4.50 — not catastrophic, but avoidable.

Anthropic's prompt caching lets you mark a content block with `cache_control: ephemeral`. If the same prefix is sent within 5 minutes, the API uses the cached attention key-value pairs instead of recomputing them. Cache reads cost 10% of normal input pricing. The trade-off is a 25% premium on the first write, but from the second request onward in an active session, the history block costs 90% less. This makes the rolling-window memory feature nearly cost-neutral compared to having no memory at all.

The 5-minute TTL means the cache is cold when a user returns the next day. The conversation history is still fetched from DynamoDB and sent to Claude, just at full price for that first request. From the second question onward in that session, caching kicks in again.

**3. What was the hardest production bug to debug?**

The naming conflict with `qdrant_client.py`. Python's import system resolves module names against files in the current directory before checking installed packages. The worker service had a file named `qdrant_client.py` — which shadowed the `qdrant-client` pip package of the same name. When `vector_store.py` did `from qdrant_client import QdrantClient`, Python found our own file first and tried to import `QdrantClient` from it — raising `ImportError: cannot import name 'QdrantClient' from partially initialized module 'qdrant_client'`.

The error message was misleading because it mentioned a "partially initialized module," which usually indicates a circular import. I spent time looking for circular imports before noticing the file name collision. The fix was renaming our file to `vector_store.py`. This is the kind of bug that is obvious in hindsight but nearly invisible when you're staring at a stack trace that points to a file you wrote.

---

### 10-Minute Deep Dive

#### The Problem Being Solved

Most RAG implementations answer: "Given a question, find the most similar text and summarize it." That is useful for document Q&A. It is not useful for research synthesis, where the value is understanding *disagreement* between sources — not just retrieving relevant content.

A researcher asking "Should I use vLLM or llama.cpp for production inference?" does not want the top-5 most similar chunks from a combined corpus. They want to know what the academic community has measured experimentally, what ML engineers have discovered in production at scale, and what the actual codebases offer in terms of features and trade-offs. These three perspectives often contradict each other, and surfacing that contradiction is more valuable than hiding it behind a confident-sounding summary.

MARS is built around that thesis. The Critic agent is not just a summarizer — it is an adversarial reader looking for inconsistencies across sources. That is the core product differentiator.

#### Architecture Journey and Failures

**Attempt 1: Single-process, no queue.** The first working version ran all three retrievers in-process using `asyncio.gather`. It worked locally. The problem: if any retriever threw an exception, all three failed together. There was no retry, no isolation, no observability. Any upstream API rate limit (GitHub, HN Algolia, arXiv) propagated as a hard failure to the user. The async gather approach also cannot scale — adding a fourth source type requires deploying a new version of the entire orchestrator.

**Attempt 2: SQS + separate worker.** Moved retrieval to a worker service that long-polls SQS. Each sub-question becomes a message with a `correlation_id`. The orchestrator publishes 3 messages and polls DynamoDB until all 3 results arrive or the timeout (30 seconds) elapses. This decouples the orchestrator from the retrievers completely. A GitHub rate limit causes one message to fail and requeue — the other two retrievers succeed and their results are still returned. The Critic synthesizes with partial data and assigns Low confidence. The user gets an answer instead of a 500 error.

**Attempt 3: Naming conflict crash.** Worker deployment failed with `ImportError: cannot import name 'QdrantClient' from partially initialized module 'qdrant_client'`. Root cause: our file `qdrant_client.py` shadowed the pip package. Renamed to `vector_store.py`. This was a 45-minute debug session that ended with a one-word fix.

**Attempt 4: Qdrant API version mismatch.** Upgraded `qdrant-client` to v1.17 for bug fixes. The `.search()` method was removed. Had to update all search calls to `.query_points()` with the new response structure (`response.points` instead of a direct list). API changelogs are not optional reading.

**Attempt 5: Filtered search with no index.** Qdrant returned HTTP 400: "Index required but not found for field 'source'." Vector similarity search works without indexes. Filtered search (where you filter by a payload field before or after ANN) requires a payload index on that field. Added `client.create_payload_index()` call to `ensure_collection()`. Now idempotent on every startup.

**Attempt 6: Invalid point IDs.** Qdrant requires point IDs to be either unsigned integers or UUIDs. The chunker was generating hex strings from SHA-256 digests. Qdrant rejected them as invalid. Changed ID generation to `uuid.UUID(bytes=digest[:16])` which produces a valid UUID from the same deterministic hash.

**Attempt 7: JSON truncation from Claude.** The Critic was hitting `max_tokens=2048` and cutting off mid-JSON. The response would be `{"answer": "...", "sources": [{"source": "arxiv"` — terminated in the middle of a string. `json.loads()` raised `JSONDecodeError: Unterminated string`. Raised `max_tokens` to 4096 and added chunk text truncation at 600 chars per chunk to keep the prompt size manageable. Both fixes together eliminated the truncation.

**Attempt 8: GitHub API 401 on ingestion.** The `.env` had `GITHUB_TOKEN=ghp_...` as a placeholder. The fetcher sent this as a Bearer token. GitHub returned 401. Unauthenticated GitHub API requests work for search endpoints (rate-limited to 10/min, sufficient for ingestion). Fixed by clearing the placeholder and adding error handling so a GitHub auth failure returns an empty list instead of crashing the entire ingestion pipeline.

#### Numbers

- **Qdrant collection**: 210+ chunks, 384-dimensional vectors (all-MiniLM-L6-v2), cosine similarity
- **Chunk size**: 512 tokens ≈ 2,048 characters, 50-token overlap
- **Embedding latency**: ~50ms locally (MPS on Apple Silicon), ~80ms on CPU in ECS Fargate
- **Claude decompose latency**: ~1-2 seconds (512 max_tokens)
- **Claude critic latency**: ~5-12 seconds (4096 max_tokens, 3 source blocks)
- **End-to-end latency**: 8-15 seconds (local mode, no SQS overhead)
- **Test coverage**: 12 unit tests (4 critic/prompt tests, 4 chunker tests, 4 embedder tests)
- **Infrastructure**: 1 VPC, 2 public subnets, 1 ALB, 1 ECS cluster, 3 ECS services, 4 ECR repos, 2 DynamoDB tables, 1 SQS queue, 1 S3 bucket, 4 Secrets Manager secrets
- **GitHub Actions**: CI ~6 min, deploy ~20 min per push to main
- **Monthly cost**: $42-47/month at 24/7 uptime, $15-20/month with overnight scaling

#### What Would Be Done Differently

**Auth from day one.** The localStorage UUID approach works for single-device use and is genuinely privacy-preserving. But it breaks on multi-device access, which matters for a recruiter who might check this on their phone after seeing it on a laptop. AWS Cognito with a simple email/magic-link flow would have taken 2-3 days to implement and made the session model significantly more robust. The cost is zero (50,000 MAU free tier).

**Structured logging from day one.** All services log to CloudWatch via `awslogs`. The log format is unstructured Python logging — `INFO:__main__: Wrote 5 chunks to DynamoDB`. This is human-readable but not machine-queryable. If you want to know the average number of chunks returned per session over the last week, you cannot write a CloudWatch Insights query against unstructured logs. JSON-structured logs (`{"level": "INFO", "chunks": 5, "correlation_id": "..."}`) would have made operational observability trivial.

**Worker memory sizing.** The worker Fargate task is provisioned at 0.25 vCPU and 0.5GB RAM. `all-MiniLM-L6-v2` loads into memory once on startup (~90MB). But if the sentence-transformers library updates and the model size increases, or if batch sizes grow, 0.5GB becomes a constraint. 1GB would have cost $4.44 more per month — a reasonable buffer for a model that lives in RAM.

**Content extraction for arXiv.** The arXiv API returns abstracts, not full paper text. A paper's abstract is ~300 words — one chunk. The system works because abstracts are dense with key terminology and claims. But a question about the mathematical formulation of a technique in a paper will not be answered well from an abstract. Full-text extraction via PDF parsing (PyMuPDF) would have been the right call for research depth, at the cost of significantly more complex ingestion logic.

#### Stakeholder and Management Perspective

This system was built as a portfolio artifact to demonstrate production-readiness to technical interviewers. The design decisions were made with that audience in mind:

- **Terraform over manual AWS Console clicks**: reproducibility is the point. An interviewer can clone the repo, fill in credentials, run `terraform apply`, and have a running system in 5 minutes. Manual console configuration cannot be demonstrated in a code review.

- **No orchestration frameworks**: interviewers at senior levels often ask "what does LangChain actually do?" The answer is: what we built manually. Being able to point to a 50-line `orchestrator.py` and explain every line is more impressive than saying "I used LangChain's `AgentExecutor` class."

- **Cost visibility**: every architectural decision in this project has a dollar amount attached to it. SQS vs direct HTTP is not just a resilience argument — SQS is free for the first million requests per month. RDS vs DynamoDB is not just a data model argument — DynamoDB's free tier covers this project indefinitely. Engineering judgment that ignores cost is incomplete engineering judgment.

- **The contradiction detection feature**: most AI demos generate answers. This system generates answers and then questions them. That distinction — building a system that is critical of its own outputs — is the highest-signal technical differentiator in the project from a research and systems design perspective.
