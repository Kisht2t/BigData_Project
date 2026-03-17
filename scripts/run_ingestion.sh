#!/bin/bash
# Run the full ingestion pipeline locally (outside Docker)
# Usage: ./scripts/run_ingestion.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f "$ROOT/.env" ]; then
  echo "Error: .env file not found. Copy .env.example and fill it in."
  exit 1
fi

source "$ROOT/.env"

export PYTHONPATH="$ROOT/backend/shared:$ROOT/backend/worker:$PYTHONPATH"

echo "Starting ingestion pipeline..."
cd "$ROOT/ingestion"
python pipeline.py

echo "Ingestion complete."
