#!/bin/bash
# Build Docker images, push to ECR, and trigger ECS rolling deploy
# Usage: ./scripts/deploy.sh
# Requires: AWS CLI configured, ECR repos created via Terraform

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
TAG="${1:-$(git rev-parse --short HEAD)}"

echo "Deploying tag: $TAG"
echo "ECR: $ECR"

# Log in to ECR
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Build and push orchestrator
echo "Building orchestrator..."
docker build -f "$ROOT/backend/orchestrator/Dockerfile" \
  -t "$ECR/mars-orchestrator:$TAG" \
  -t "$ECR/mars-orchestrator:latest" \
  "$ROOT"
docker push "$ECR/mars-orchestrator:$TAG"
docker push "$ECR/mars-orchestrator:latest"

# Build and push worker
echo "Building worker..."
docker build -f "$ROOT/backend/worker/Dockerfile" \
  -t "$ECR/mars-worker:$TAG" \
  -t "$ECR/mars-worker:latest" \
  "$ROOT"
docker push "$ECR/mars-worker:$TAG"
docker push "$ECR/mars-worker:latest"

# Build and push frontend
echo "Building frontend..."
docker build -f "$ROOT/frontend/Dockerfile" \
  -t "$ECR/mars-frontend:$TAG" \
  -t "$ECR/mars-frontend:latest" \
  "$ROOT/frontend"
docker push "$ECR/mars-frontend:$TAG"
docker push "$ECR/mars-frontend:latest"

# Trigger ECS rolling deploys
echo "Deploying to ECS..."
for SERVICE in mars-orchestrator mars-worker mars-frontend; do
  aws ecs update-service \
    --cluster mars-cluster \
    --service "$SERVICE" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --output text --query 'service.serviceName'
done

echo "Waiting for services to stabilize..."
aws ecs wait services-stable \
  --cluster mars-cluster \
  --services mars-orchestrator mars-worker mars-frontend \
  --region "$AWS_REGION"

echo "Deploy complete. Tag: $TAG"
