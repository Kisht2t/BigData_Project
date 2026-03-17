# Multi-Agent Research Synthesizer

## Project Overview
A portfolio-grade Big Data project that goes beyond a typical RAG demo. Users ask complex tech/science questions and a multi-agent pipeline answers them by:
1. **Orchestrator Agent** (Claude) — decomposes the question into 3 targeted sub-questions
2. **Retriever Workers** — search Qdrant vector DB across 3 specialized sources (arXiv, Hacker News, GitHub)
3. **Critic Agent** (Claude) — cross-validates all retrieved chunks, detects contradictions, assigns confidence scores, and returns a synthesized answer with a source attribution map

**Domain**: Tech & Science News
**Key differentiator**: Async multi-agent orchestration via SQS + contradiction detection — not a simple "embed → query → answer" chain

---

## Architecture

```
User Question
  ↓
API Gateway (HTTP API)
  ↓
ECS Fargate: Orchestrator API (FastAPI)
  → Claude decomposes question → 3 sub-questions
  → Publishes to SQS (tagged: arxiv | hackernews | github)
  ↓
ECS Fargate: Retriever Worker (polls SQS)
  ├─ arXiv retriever
  ├─ Hacker News retriever
  └─ GitHub README retriever
       → sentence-transformers (embedding, in-container)
       → Qdrant Cloud (vector search)
       → DynamoDB (write results keyed by correlation_id)
  ↓
Orchestrator collects results → Claude Critic Agent
  → Contradiction detection, confidence scoring, citations
  ↓
Streamlit Frontend: chat UI + source attribution + confidence panel

Supporting AWS services:
  S3          → raw ingested documents, ingestion cache
  SQS         → agent message queue
  DynamoDB    → conversation history, retrieval results
  CloudWatch  → logs, metrics, alarms
  ECR         → Docker images
  Secrets Manager → API keys
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| API Framework | FastAPI + uvicorn |
| Agent LLM | Claude claude-sonnet-4-6 (Anthropic API) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | Qdrant Cloud (free tier) |
| Queue | AWS SQS |
| Storage | AWS S3 |
| Database | AWS DynamoDB |
| Frontend | Streamlit |
| Containers | Docker + ECS Fargate |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Monitoring | AWS CloudWatch |
| Local Dev | Docker Compose |

---

## Project Structure

```
BigData_Project/
├── backend/
│   ├── orchestrator/         # FastAPI service — question decomposition + synthesis
│   │   ├── main.py           # FastAPI app entrypoint
│   │   ├── agents/
│   │   │   ├── orchestrator.py   # Claude: decomposes question, dispatches to SQS
│   │   │   ├── critic.py         # Claude: cross-validates, detects contradictions
│   │   │   └── prompts.py        # All Claude prompt templates
│   │   ├── api/
│   │   │   └── routes.py         # /ask, /ingest endpoints
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic request/response models
│   │   └── Dockerfile
│   ├── worker/               # Retriever worker — polls SQS, searches Qdrant
│   │   ├── main.py           # SQS long-poll loop
│   │   ├── retrievers/
│   │   │   ├── arxiv.py
│   │   │   ├── hackernews.py
│   │   │   └── github.py
│   │   ├── embedder.py       # sentence-transformers wrapper
│   │   ├── qdrant_client.py  # Qdrant Cloud wrapper
│   │   └── Dockerfile
│   └── shared/               # Shared code between orchestrator + worker
│       ├── models.py         # Shared Pydantic models (AgentTask, RetrievalResult)
│       └── aws_clients.py    # Boto3 client factories (SQS, DynamoDB, S3, Secrets)
├── ingestion/                # Data ingestion pipeline
│   ├── pipeline.py           # Entry point: fetch → chunk → embed → upsert
│   ├── sources/
│   │   ├── arxiv_fetcher.py  # arXiv API client
│   │   ├── hn_fetcher.py     # Hacker News Algolia API client
│   │   └── github_fetcher.py # GitHub API — trending repos READMEs
│   ├── chunker.py            # Text chunking (512 tokens, 50 overlap)
│   ├── embedder.py           # sentence-transformers embedding
│   └── Dockerfile
├── frontend/
│   ├── app.py                # Streamlit entrypoint
│   ├── components/
│   │   ├── chat.py           # Chat UI component
│   │   ├── source_map.py     # Source attribution panel
│   │   └── confidence.py     # Confidence + contradiction display
│   └── Dockerfile
├── infrastructure/           # Terraform IaC
│   ├── main.tf               # Root module, provider config
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── ecs/              # ECS cluster, task definitions, services
│   │   ├── networking/       # VPC, subnets, security groups, API Gateway
│   │   ├── storage/          # S3, DynamoDB, SQS
│   │   └── iam/              # IAM roles and policies for ECS tasks
│   └── terraform.tfvars.example
├── scripts/
│   ├── run_ingestion.sh      # Trigger ingestion pipeline locally
│   └── deploy.sh             # Build + push images, trigger ECS deploy
├── .github/
│   └── workflows/
│       ├── ci.yml            # Test + lint on PR
│       └── deploy.yml        # Build → ECR → ECS redeploy on main push
├── docker-compose.yml        # Local development (all services)
├── CLAUDE.md                 # This file
├── .env.example              # Required environment variables
└── README.md
```

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- Python 3.12 (for running scripts outside containers)
- AWS CLI configured (for AWS service access)

### Setup
```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Start all services locally
docker-compose up --build

# 3. Services available at:
#    Orchestrator API:  http://localhost:8000
#    API Docs (Swagger): http://localhost:8000/docs
#    Next.js Frontend:   http://localhost:3001
#    Qdrant Dashboard:  http://localhost:6333/dashboard (if running local Qdrant)
```

### Run Ingestion
```bash
# Populate Qdrant with seed data (arXiv + HN + GitHub)
./scripts/run_ingestion.sh

# Or trigger a single URL ingestion via API
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/abs/2310.06825"}'
```

### Run Tests
```bash
# From project root
docker-compose run --rm orchestrator pytest tests/
docker-compose run --rm worker pytest tests/

# Or with local Python
cd backend/orchestrator && pytest tests/ -v
```

---

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (get from console.anthropic.com) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `SQS_QUEUE_URL` | SQS queue URL for agent tasks |
| `DYNAMODB_TABLE_NAME` | DynamoDB table for results + history |
| `S3_BUCKET_NAME` | S3 bucket for raw documents |

---

## AWS Deployment

### Prerequisites
- Terraform >= 1.6
- AWS CLI with credentials configured
- GitHub repository with secrets set

### Deploy Infrastructure
```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

### Build and Push Images
```bash
./scripts/deploy.sh
```

### GitHub Actions CI/CD
- **`ci.yml`**: Runs on every PR — pytest + ruff lint
- **`deploy.yml`**: Runs on push to `main` — builds Docker images, pushes to ECR, triggers ECS service update

---

## Code Conventions

- **Python 3.12** with full type hints on all functions
- **Pydantic v2** models for all request/response schemas
- **Async FastAPI** — all route handlers are `async def`
- **Ruff** for linting (`ruff check .`)
- **pytest** for tests — unit tests mock AWS clients and Qdrant
- **No LangChain/LlamaIndex** — Claude API called directly for full control and transparency
- Shared models live in `backend/shared/models.py` — import from there, never redefine

### AWS Resource Naming Convention
All resources prefixed with `mars-` (Multi-Agent Research Synthesizer):
- ECS Cluster: `mars-cluster`
- SQS Queue: `mars-agent-tasks`
- DynamoDB Table: `mars-results`
- S3 Bucket: `mars-documents-{account_id}`
- ECR Repos: `mars-orchestrator`, `mars-worker`, `mars-frontend`, `mars-ingestion`

### Qdrant Collections
- `tech_news` — all ingested documents, filtered by `source` metadata field
  - `source` values: `arxiv`, `hackernews`, `github`

---

## Monthly Cost Tracking

| Resource | Monthly Est. |
|---|---|
| ECS Fargate (3 services, 24/7) | ~$35.55 |
| ECS Fargate (ingestion, scheduled) | ~$0.50 |
| S3, SQS, DynamoDB | ~$0.50 |
| API Gateway, ECR, CloudWatch | ~$2.00 |
| Secrets Manager, data transfer | ~$2.00 |
| Claude API (usage) | ~$2-5 |
| Qdrant Cloud | $0 |
| **Total** | **~$42-47/month** |

**Cost tip**: Use ECS scheduled scaling to run 0 tasks overnight (e.g. 10pm–8am) → reduces to ~$15-20/month.

---

## Key Design Decisions

1. **No orchestration framework** (no LangChain): Claude API called directly. Easier to debug, full prompt visibility, no magic abstractions.
2. **SQS for agent communication**: Decouples orchestrator from workers. Workers can scale independently. Resilient to worker failures (messages re-queued).
3. **DynamoDB for result collection**: Orchestrator polls DynamoDB for retrieval results (keyed by `correlation_id`). Clean, serverless, no shared state.
4. **sentence-transformers in-container**: Free embeddings, no per-token cost, consistent across ingestion and retrieval.
5. **Qdrant Cloud free tier**: Offloads vector DB infra entirely. 1GB is enough for demo-scale data.
6. **Terraform for IaC**: Reproducible, version-controlled infrastructure. One `terraform apply` recreates everything.
